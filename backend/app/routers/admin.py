"""
Admin Dashboard API endpoints
Provides statistics, logs, and management functions for issued certificates
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy import text

from ..services.supabase_client import SupabaseClient
from ..models import CertificateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/stats")
async def get_admin_stats():
    """Get overall statistics for the admin dashboard"""
    try:
        client = SupabaseClient()
        
        if not client.client:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        # Get total certificates count
        total_result = client.client.table("issued_certificates").select("id", count="exact").execute()
        total_count = total_result.count if total_result.count is not None else 0
        
        # Get certificates by status
        status_stats = []
        try:
            status_result = client.client.table("issued_certificates").select("status").execute()
            if status_result.data:
                from collections import Counter
                status_counts = Counter([cert["status"] for cert in status_result.data])
                status_stats = [{"status": k, "count": v} for k, v in status_counts.items()]
        except Exception as e:
            logger.error(f"Error getting status stats: {str(e)}")
        
        # Get certificates by institution (top 10)
        institution_stats = []
        try:
            institution_result = client.client.table("issued_certificates").select("institution").execute()
            if institution_result.data:
                from collections import Counter
                inst_counts = Counter([cert["institution"] for cert in institution_result.data if cert["institution"]])
                institution_stats = [{"institution": k, "count": v} for k, v in inst_counts.most_common(10)]
        except Exception as e:
            logger.error(f"Error getting institution stats: {str(e)}")
        
        # Get recent activity (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_result = client.client.table("issued_certificates").select("*").gte("created_at", seven_days_ago).execute()
        recent_count = len(recent_result.data) if recent_result.data else 0
        
        # Get certificates by year
        year_stats = []
        try:
            year_result = client.client.table("issued_certificates").select("year").execute()
            if year_result.data:
                from collections import Counter
                year_counts = Counter([cert["year"] for cert in year_result.data if cert["year"]])
                year_stats = [{"year": k, "count": v} for k, v in sorted(year_counts.items(), reverse=True)]
        except Exception as e:
            logger.error(f"Error getting year stats: {str(e)}")
        
        return {
            "total_certificates": total_count,
            "recent_certificates": recent_count,
            "status_distribution": status_stats,
            "institution_distribution": institution_stats,
            "yearly_distribution": year_stats,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        # Return mock data as fallback
        return {
            "total_certificates": 0,
            "recent_certificates": 0,
            "status_distribution": [],
            "institution_distribution": [],
            "yearly_distribution": [],
            "error": str(e),
            "last_updated": datetime.now().isoformat()
        }

@router.get("/certificates")
async def get_certificates_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    institution: Optional[str] = Query(None, description="Filter by institution"),
    search: Optional[str] = Query(None, description="Search by student name or certificate ID")
):
    """Get paginated list of certificates with filters"""
    try:
        client = SupabaseClient()
        
        if not client.client:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        # Build query
        query = client.client.table("issued_certificates").select("*")
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if institution:
            query = query.eq("institution", institution)
        if search:
            query = query.or_(f"student_name.ilike.%{search}%,certificate_id.ilike.%{search}%")
        
        # Get total count for pagination
        count_query = client.client.table("issued_certificates").select("id", count="exact")
        if status:
            count_query = count_query.eq("status", status)
        if institution:
            count_query = count_query.eq("institution", institution)
        if search:
            count_query = count_query.or_(f"student_name.ilike.%{search}%,certificate_id.ilike.%{search}%")
        
        total_result = count_query.execute()
        total_count = total_result.count if total_result.count is not None else 0
        
        # Apply pagination and ordering
        offset = (page - 1) * limit
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return {
            "certificates": result.data if result.data else [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting certificates list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_admin_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    days: int = Query(30, ge=1, le=365, description="Days to look back")
):
    """Get recent certificate activity logs"""
    try:
        client = SupabaseClient()
        
        if not client.client:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        # Get certificates from the last N days
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Apply pagination
        offset = (page - 1) * limit
        
        result = client.client.table("issued_certificates").select(
            "certificate_id, student_name, institution, status, created_at, updated_at, issued_by"
        ).gte("created_at", start_date).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count for pagination
        count_result = client.client.table("issued_certificates").select("id", count="exact").gte("created_at", start_date).execute()
        total_count = count_result.count if count_result.count is not None else 0
        
        # Transform data for logs
        logs = []
        for cert in (result.data if result.data else []):
            logs.append({
                "id": cert["certificate_id"],
                "action": "Certificate Issued",
                "details": f"Certificate issued to {cert['student_name']} from {cert['institution']}",
                "timestamp": cert["created_at"],
                "user": cert.get("issued_by", "system"),
                "status": cert["status"]
            })
        
        return {
            "logs": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting admin logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/institutions")
async def get_institutions():
    """Get list of all institutions for filter dropdown"""
    try:
        client = SupabaseClient()
        
        if not client.client:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        result = client.client.table("issued_certificates").select("institution").execute()
        
        if result.data:
            institutions = list(set([cert["institution"] for cert in result.data if cert["institution"]]))
            institutions.sort()
            return {"institutions": institutions}
        
        return {"institutions": []}
        
    except Exception as e:
        logger.error(f"Error getting institutions: {str(e)}")
        return {"institutions": [], "error": str(e)}

@router.delete("/certificates/{certificate_id}")
async def delete_certificate(certificate_id: str):
    """Delete a certificate by ID (admin only)"""
    try:
        client = SupabaseClient()
        
        if not client.client:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        # Check if certificate exists
        check_result = client.client.table("issued_certificates").select("certificate_id").eq("certificate_id", certificate_id).execute()
        
        if not check_result.data:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Delete the certificate
        result = client.client.table("issued_certificates").delete().eq("certificate_id", certificate_id).execute()
        
        return {"message": f"Certificate {certificate_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))