"""
FastAPI entrypoint with API routes for certificate verification
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from .config import settings
from .models import CertificateResponse, VerificationRequest
from .services.supabase_client import SupabaseClient
from .services.simple_fusion_engine import SimpleFusionEngine
from .services.certificate_issuance import CertificateIssuanceService
from .services.public_verification import PublicVerificationService
from .utils.helpers import setup_logging, process_image, generate_secure_token, create_qr_code

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Certificate Verifier API",
    description="AI-powered certificate verification system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
supabase_client = SupabaseClient()
fusion_engine = SimpleFusionEngine(supabase_client)
issuance_service = CertificateIssuanceService(supabase_client)
public_verification_service = PublicVerificationService(supabase_client)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Certificate Verifier API is running"}

@app.get("/test-db-schema")
async def test_db_schema():
    """Test database schema to see what columns exist"""
    try:
        # Try to get the table schema
        result = supabase_client.client.table("issued_certificates").select("*").limit(1).execute()
        return {
            "message": "Database connection successful",
            "table_exists": True,
            "sample_data": result.data if result.data else "No data in table"
        }
    except Exception as e:
        return {
            "message": "Database error",
            "error": str(e),
            "table_exists": False
        }

@app.get("/test-simple-verify/{cert_id}")
async def test_simple_verify(cert_id: str):
    """Test simple verification without /RG suffix"""
    try:
        # Clean the certificate ID (remove any suffixes)
        clean_cert_id = cert_id.split('/')[0] if '/' in cert_id else cert_id
        logger.info(f"Testing verification for cleaned certificate ID: {clean_cert_id}")
        
        # Try to find the certificate
        result = supabase_client.client.table("issued_certificates").select("*").eq("certificate_id", clean_cert_id).execute()
        
        if result.data:
            certificate = result.data[0]
            return {
                "success": True,
                "message": "Certificate found",
                "certificate_id": certificate.get('certificate_id'),
                "student_name": certificate.get('student_name'),
                "verification_url": f"http://localhost:8000/verify/{clean_cert_id}/page"
            }
        else:
            return {
                "success": False,
                "message": "Certificate not found",
                "searched_id": clean_cert_id,
                "original_id": cert_id
            }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-verification")
async def test_verification():
    """Test verification page with actual certificates from database"""
    try:
        # Get all certificates from database
        result = supabase_client.client.table("issued_certificates").select("certificate_id, student_name, course_name").limit(10).execute()
        certificates = result.data if result.data else []
        
        # Also get the latest certificate to check its QR code
        latest_cert = supabase_client.client.table("issued_certificates").select("*").order("created_at", desc=True).limit(1).execute()
        latest_cert_data = latest_cert.data[0] if latest_cert.data else None
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verification Test</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="min-h-screen bg-gray-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-6">✅ Verification Page Test</h1>
                <p class="text-lg text-gray-600 mb-6">If you can see this page, the HTML template is working correctly!</p>
                
                <div class="bg-white shadow rounded-lg p-6 mb-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4">Available Certificates in Database ({len(certificates)} found):</h2>
                    <div class="space-y-2">
        """
        
        for cert in certificates:
            cert_id = cert.get('certificate_id', 'Unknown')
            student_name = cert.get('student_name', 'Unknown')
            course_name = cert.get('course_name', 'Unknown')
            html_content += f"""
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <div class="flex-1">
                                <span class="font-mono text-sm font-medium">{cert_id}</span>
                                <span class="text-sm text-gray-600 ml-2">{student_name}</span>
                                <span class="text-xs text-gray-500 ml-2">({course_name})</span>
                            </div>
                            <a href="/verify/{cert_id}/page" class="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 bg-blue-100 rounded">Test Verify</a>
                        </div>
            """
        
        html_content += """
                    </div>
                </div>
                
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <h3 class="font-semibold text-blue-900 mb-2">Test Instructions:</h3>
                    <ol class="text-sm text-blue-800 space-y-1">
                        <li>1. Click "Test Verify" next to any certificate above</li>
                        <li>2. Or issue a new certificate and use its ID</li>
                        <li>3. Check the browser console for debug logs</li>
                    </ol>
                </div>
                
                {f'''
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h3 class="font-semibold text-yellow-900 mb-2">Latest Certificate Debug Info:</h3>
                    <div class="text-sm text-yellow-800">
                        <p><strong>Certificate ID:</strong> {latest_cert_data.get('certificate_id', 'None') if latest_cert_data else 'No certificates found'}</p>
                        <p><strong>Student Name:</strong> {latest_cert_data.get('student_name', 'None') if latest_cert_data else 'No certificates found'}</p>
                        <p><strong>Expected Verification URL:</strong> http://localhost:8000/verify/{latest_cert_data.get('certificate_id', 'N/A') if latest_cert_data else 'N/A'}/page</p>
                        <p><strong>Created At:</strong> {latest_cert_data.get('created_at', 'None') if latest_cert_data else 'No certificates found'}</p>
                    </div>
                </div>
                ''' if latest_cert_data else ''}
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/list-certificates")
async def list_certificates():
    """List all certificates in the database"""
    try:
        result = supabase_client.client.table("issued_certificates").select("certificate_id, student_name, course_name, institution, created_at").execute()
        
        if not result.data:
            return {"message": "No certificates found", "certificates": []}
        
        return {
            "message": f"Found {len(result.data)} certificates",
            "certificates": result.data
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/certificate/{certificate_id}")
async def get_certificate_details(certificate_id: str):
    """Get detailed certificate information for frontend display"""
    try:
        logger.info(f"Fetching certificate details for: {certificate_id}")
        
        # Get certificate from database
        result = supabase_client.client.table("issued_certificates").select("*").eq("certificate_id", certificate_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        certificate = result.data[0]
        
        # Get attestation if exists
        attestation_result = supabase_client.client.table("attestations").select("*").eq("verification_id", certificate.get("id")).execute()
        attestation = attestation_result.data[0] if attestation_result.data else None
        
        # Prepare response
        response_data = {
            "certificate_id": certificate.get("certificate_id"),
            "student_name": certificate.get("student_name"),
            "roll_number": certificate.get("roll_number"),
            "course_name": certificate.get("course_name"),
            "institution": certificate.get("institution"),
            "issue_date": certificate.get("issue_date"),
            "year": certificate.get("year"),
            "grade": certificate.get("grade"),
            "status": certificate.get("status"),
            "certificate_image_url": certificate.get("image_url"),
            "image_url": certificate.get("image_url"),
            "verification_url": f"http://localhost:8000/verify/{certificate_id}/page",
            "created_at": certificate.get("created_at"),
            "attestation": attestation
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching certificate details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching certificate: {str(e)}")

@app.get("/verify/{certificate_id}")
async def verify_certificate(certificate_id: str):
    """Verify certificate by ID and show all details"""
    try:
        # Get certificate from database
        result = supabase_client.client.table("issued_certificates").select("*").eq("certificate_id", certificate_id).execute()
        
        if not result.data:
            return {
                "success": False,
                "message": "Certificate not found",
                "certificate_id": certificate_id
            }
        
        certificate = result.data[0]
        
        # Get attestation if exists
        attestation_result = supabase_client.client.table("attestations").select("*").eq("verification_id", certificate.get("id")).execute()
        attestation = attestation_result.data[0] if attestation_result.data else None
        
        return {
            "success": True,
            "certificate": certificate,
            "attestation": attestation,
            "verification_url": f"/verify/{certificate_id}",
            "message": "Certificate verified successfully"
        }
        
    except Exception as e:
        logger.error(f"Certificate verification failed: {str(e)}")
        return {
            "success": False,
            "message": f"Verification failed: {str(e)}",
            "certificate_id": certificate_id
        }

@app.get("/verify/{certificate_id}/page")
async def verify_certificate_page(certificate_id: str, request: Request = None):
    """Serve HTML verification page for certificate"""
    try:
        # Clean the certificate ID (remove any suffixes like /RG)
        original_cert_id = certificate_id
        clean_cert_id = certificate_id.split('/')[0] if '/' in certificate_id else certificate_id
        
        logger.info(f"Verification page requested for certificate: {original_cert_id}")
        logger.info(f"Cleaned certificate ID: {clean_cert_id}")
        logger.info(f"Certificate ID type: {type(clean_cert_id)}")
        logger.info(f"Certificate ID value: {repr(clean_cert_id)}")
        
        # Log verification attempt
        try:
            client_ip = request.client.host if request else "unknown"
            user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
            
            supabase_client.client.table("verification_logs").insert({
                "certificate_id": clean_cert_id,
                "verification_id": f"VER_{generate_secure_token(8)}",
                "status": "pending",
                "ip_address": client_ip,
                "user_agent": user_agent,
                "verification_method": "qr_scan"
            }).execute()
        except Exception as log_error:
            logger.warning(f"Failed to log verification attempt: {log_error}")
        
        # Get certificate from database using cleaned ID
        result = supabase_client.client.table("issued_certificates").select("*").eq("certificate_id", clean_cert_id).execute()
        
        logger.info(f"Database query result: {result.data}")
        logger.info(f"Query executed for certificate_id: {certificate_id}")
        
        # Also try to find any certificates with similar IDs
        all_certs = supabase_client.client.table("issued_certificates").select("certificate_id").limit(10).execute()
        logger.info(f"Sample certificate IDs in database: {[c.get('certificate_id') for c in all_certs.data]}")
        
        if not result.data:
            logger.warning(f"No certificate found for ID: {clean_cert_id} (original: {original_cert_id})")
            
            # Update verification log to failed
            try:
                supabase_client.client.table("verification_logs").update({
                    "status": "failed",
                    "error_message": "Certificate not found"
                }).eq("certificate_id", clean_cert_id).execute()
            except Exception as log_error:
                logger.warning(f"Failed to update verification log: {log_error}")
            
            html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Certificate Not Found</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="min-h-screen bg-gray-50 flex items-center justify-center">
                    <div class="max-w-md w-full mx-4 bg-white rounded-lg shadow-md p-6 text-center">
                        <div class="p-3 rounded-full bg-red-500 mx-auto mb-4 w-16 h-16 flex items-center justify-center">
                            <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </div>
                            <h1 class="text-2xl font-bold text-red-900 mb-2">Certificate Not Found</h1>
                            <p class="text-sm text-gray-600 mb-2">Original ID: <span class="font-mono bg-gray-100 px-2 py-1 rounded">{original_cert_id}</span></p>
                            <p class="text-sm text-gray-600 mb-4">Cleaned ID: <span class="font-mono bg-gray-100 px-2 py-1 rounded">{clean_cert_id}</span></p>
                            <p class="text-sm text-gray-500">The requested certificate could not be found in our database.</p>
                    </div>
                </body>
                </html>
                """
            return HTMLResponse(content=html_content)
        
        certificate = result.data[0]
        logger.info(f"Found certificate: {certificate.get('certificate_id', 'Unknown')}")
        logger.info(f"Certificate ID type: {type(certificate.get('certificate_id'))}")
        logger.info(f"Certificate ID value: {repr(certificate.get('certificate_id'))}")
        
        # Update verification log to successful
        try:
            supabase_client.client.table("verification_logs").update({
                "status": "verified"
            }).eq("certificate_id", clean_cert_id).execute()
        except Exception as log_error:
            logger.warning(f"Failed to update verification log: {log_error}")
        
        # Get attestation if exists
        attestation_result = supabase_client.client.table("attestations").select("*").eq("verification_id", certificate.get("id")).execute()
        attestation = attestation_result.data[0] if attestation_result.data else None
        logger.info(f"Attestation found: {attestation is not None}")
        
        # Create HTML page
        html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Certificate Verification - {certificate.get('certificate_id', 'Unknown')}</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                    <script>
                        tailwind.config = {{
                            theme: {{
                                extend: {{
                                    colors: {{
                                        primary: '#3b82f6',
                                        secondary: '#6b7280',
                                        success: '#10b981',
                                        warning: '#f59e0b',
                                        danger: '#ef4444'
                                    }}
                                }}
                            }}
                        }}
                    </script>
                </head>
                <body class="min-h-screen bg-gray-50">
                    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                        <!-- Header -->
                        <div class="bg-white shadow rounded-lg mb-6">
                            <div class="px-6 py-4 border-b border-gray-200">
                                <div class="flex items-center">
                                    <div class="p-3 rounded-full bg-green-500">
                                        <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                    </div>
                                    <div class="ml-4">
                                        <h1 class="text-2xl font-bold text-gray-900">Certificate Verification</h1>
                                        <p class="text-sm text-gray-500">Digital Certificate Verification System</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <!-- Certificate Image Section -->
                            <div class="bg-white shadow rounded-lg">
                                <div class="px-6 py-4 border-b border-gray-200">
                                    <h3 class="text-lg font-medium text-gray-900 flex items-center">
                                        <svg class="h-5 w-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                        </svg>
                                        Certificate
                                    </h3>
                                </div>
                                <div class="p-6">
                                    <div class="text-center">
                                        <img src="{certificate.get('image_url', '')}" 
                                             alt="Certificate" 
                                             class="max-w-full h-auto rounded-lg shadow-md mx-auto"
                                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                                        <div style="display:none;" class="p-8 text-center text-gray-500">
                                            <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                            </svg>
                                            <p class="text-sm">Certificate image not available</p>
                                            <p class="text-xs text-gray-400 mt-2">Image URL: {certificate.get('image_url', 'N/A')}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Certificate Details Section -->
                            <div class="bg-white shadow rounded-lg">
                                <div class="px-6 py-4 border-b border-gray-200">
                                    <h3 class="text-lg font-medium text-gray-900 flex items-center">
                                        <svg class="h-5 w-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                                        </svg>
                                        Certificate Details
                                    </h3>
                                </div>
                                <div class="p-6 space-y-4">
                                    <div class="grid grid-cols-1 gap-4">
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Certificate ID</span>
                                            <span class="text-sm font-mono text-gray-900">{certificate.get('certificate_id', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Student Name</span>
                                            <span class="text-sm text-gray-900">{certificate.get('student_name', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Roll Number</span>
                                            <span class="text-sm text-gray-900">{certificate.get('roll_number', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Course</span>
                                            <span class="text-sm text-gray-900">{certificate.get('course_name', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Institution</span>
                                            <span class="text-sm text-gray-900">{certificate.get('institution', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Year</span>
                                            <span class="text-sm text-gray-900">{certificate.get('year', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Grade</span>
                                            <span class="text-sm text-gray-900">{certificate.get('grade', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg">
                                            <span class="text-sm font-medium text-gray-500">Issue Date</span>
                                            <span class="text-sm text-gray-900">{certificate.get('issue_date', 'N/A')}</span>
                                        </div>
                                        <div class="flex justify-between items-center py-3 px-4 bg-green-50 rounded-lg border border-green-200">
                                            <span class="text-sm font-medium text-green-700">Status</span>
                                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                                                </svg>
                                                Verified
                                            </span>
                                        </div>
                                    </div>

                                    <!-- Verification Information -->
                                    <div class="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                                        <h4 class="text-sm font-medium text-green-800 mb-2 flex items-center">
                                            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                                            </svg>
                                            Verification Information
                                        </h4>
                                        <p class="text-sm text-green-700 mb-2">This certificate has been digitally verified and is authentic.</p>
                                        <div class="text-xs text-green-600">
                                            <p><strong>Verification URL:</strong></p>
                                            <p class="font-mono bg-white p-2 rounded border break-all">http://localhost:8000/verify/{clean_cert_id}/page</p>
                                            <p class="mt-2">Certificate verified on: {certificate.get('created_at', 'N/A')}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Certificate verification page failed: {str(e)}")
        error_html = f"""
               <!DOCTYPE html>
               <html>
               <head>
                   <title>Verification Error</title>
                   <meta charset="UTF-8">
                   <meta name="viewport" content="width=device-width, initial-scale=1.0">
                   <script src="https://cdn.tailwindcss.com"></script>
               </head>
               <body class="min-h-screen bg-gray-50 flex items-center justify-center">
                   <div class="max-w-md w-full mx-4 bg-white rounded-lg shadow-md p-6 text-center">
                       <div class="p-3 rounded-full bg-red-500 mx-auto mb-4 w-16 h-16 flex items-center justify-center">
                           <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                           </svg>
                       </div>
                       <h1 class="text-2xl font-bold text-red-900 mb-2">Verification Error</h1>
                       <p class="text-sm text-gray-600">An error occurred while verifying the certificate:</p>
                       <p class="text-xs text-gray-500 mt-2 font-mono bg-gray-100 p-2 rounded">{str(e)}</p>
                   </div>
               </body>
               </html>
               """
        return HTMLResponse(content=error_html)

@app.post("/upload", response_model=CertificateResponse)
async def upload_certificate(file: UploadFile = File(...)):
    """Upload and process certificate image"""
    try:
        # Read the uploaded file as bytes
        file_content = await file.read()
        
        # Run through fusion engine for verification
        result = await fusion_engine.verify_certificate(file_content)
        
        return result
    except Exception as e:
        logger.error(f"Error processing certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify", response_model=CertificateResponse)
async def verify_certificate(request: VerificationRequest):
    """Verify certificate using manual input or image URL"""
    try:
        result = await fusion_engine.verify_certificate_by_data(request)
        return result
    except Exception as e:
        logger.error(f"Error verifying certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    """Get certificate details by ID"""
    try:
        result = await supabase_client.get_certificate(certificate_id)
        if not result:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return result
    except Exception as e:
        logger.error(f"Error retrieving certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# UNIVERSITY CERTIFICATE ISSUANCE ENDPOINTS
# =============================================

@app.post("/issue/certificate")
async def issue_certificate(file: UploadFile = File(...), certificate_data: str = Form(None)):
    """Issue a new certificate with QR code generation and Supabase storage"""
    try:
        import json
        from datetime import datetime
        
        # Debug logging
        logger.info(f"Raw certificate_data parameter: {certificate_data}")
        logger.info(f"Type of certificate_data: {type(certificate_data)}")
        
        # Parse certificate data
        cert_data = json.loads(certificate_data) if certificate_data else {}
        
        # Debug logging
        logger.info(f"Parsed certificate data: {cert_data}")
        logger.info(f"Certificate data keys: {list(cert_data.keys())}")
        logger.info(f"Student name: {cert_data.get('student_name')}")
        logger.info(f"Course name: {cert_data.get('course_name')}")
        logger.info(f"Institution name: {cert_data.get('institution_name')}")
        
        # Read the uploaded file as bytes
        file_content = await file.read()
        
        # Generate a unique certificate ID
        certificate_id = f"CERT_{generate_secure_token(8)}"
        
        # Validate required fields
        required_fields = ["student_name", "course_name", "institution_name"]
        missing_fields = [field for field in required_fields if not cert_data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Prepare certificate data for issuance service
        certificate_data_for_issuance = {
            "certificate_id": certificate_id,
            "student_name": cert_data.get("student_name", ""),
            "roll_no": cert_data.get("roll_no", ""),
            "course_name": cert_data.get("course_name", ""),
            "institution": cert_data.get("institution_name", ""),
            "department": cert_data.get("department", ""),
            "year": cert_data.get("year_of_passing", ""),
            "grade": cert_data.get("grade", ""),
            "cgpa": cert_data.get("cgpa", ""),
            "issue_date": cert_data.get("issue_date", datetime.now().strftime("%Y-%m-%d")),
            "additional_data": cert_data.get("additional_fields", {}),
            "image_data": file_content,  # Store the image data
            "image_filename": file.filename,
            "image_content_type": file.content_type
        }
        
        logger.info(f"Issuing certificate for student: {cert_data.get('student_name', 'Unknown')}")
        
        # Use the real CertificateIssuanceService
        try:
            result = await issuance_service.issue_certificate(
                certificate_data_for_issuance, 
                institution_id="default"  # You can make this dynamic based on user
            )
        except Exception as issuance_error:
            logger.error(f"Certificate issuance service failed: {str(issuance_error)}")
            
            # If it's a database schema issue, provide helpful error message
            if "additional_data" in str(issuance_error) or "PGRST204" in str(issuance_error):
                raise HTTPException(
                    status_code=500, 
                    detail="Database schema issue detected. Please run the database migration script: backend/migrations/add_missing_columns.sql"
                )
            else:
                raise issuance_error
        
        logger.info(f"Certificate issued successfully: {result.get('certificate_id', 'Unknown ID')}")
        
        # Return the result from the service
        return {
            "success": True,
            "certificate_id": result.get("certificate_id"),
            "attestation_id": result.get("attestation_id"),
            "qr_code_url": result.get("qr_code_url"),
            "certificate_image_url": result.get("certificate_image_url"),
            "pdf_url": result.get("pdf_url"),
            "verification_url": result.get("verification_url"),
            "message": "Certificate issued successfully and stored in database",
            "certificate_data": cert_data
        }
        
    except Exception as e:
        logger.error(f"Certificate issuance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issue/bulk")
async def bulk_issue_certificates(certificates_data: dict, institution_id: str = "default"):
    """Bulk issue certificates from CSV/ERP data"""
    try:
        certificates_list = certificates_data.get("certificates", [])
        if not certificates_list:
            raise HTTPException(status_code=400, detail="No certificates data provided")
        
        result = await issuance_service.bulk_issue_certificates(certificates_list, institution_id)
        return result
    except Exception as e:
        logger.error(f"Bulk certificate issuance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-csv-parsing")
async def test_csv_parsing(file: UploadFile = File(...)):
    """Test CSV parsing and show column mapping"""
    try:
        import csv
        import io
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        csv_columns = csv_reader.fieldnames
        
        # Get first few rows
        rows = []
        for i, row in enumerate(csv_reader):
            if i >= 3:  # Only get first 3 rows
                break
            rows.append(row)
        
        return {
            "columns": csv_columns,
            "sample_rows": rows,
            "total_columns": len(csv_columns)
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload/bulk-csv")
async def upload_bulk_csv(file: UploadFile = File(...), institution_id: str = "default"):
    """Upload CSV file and process bulk certificate issuance"""
    try:
        import csv
        import io
        from datetime import datetime
        
        # Check file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        certificates_data = []
        
        # Get the actual column names from CSV
        csv_columns = csv_reader.fieldnames
        logger.info(f"CSV columns found: {csv_columns}")
        
        # Map CSV columns to our expected fields (more flexible mapping)
        column_mapping = {
            'certificate': 'certificate_id',
            'student_na': 'student_name',
            'student': 'student_name', 
            'n:': 'roll_no',
            'course_na': 'course_name',
            'course_': 'course_name',
            'na': 'institution_name',
            'institution': 'institution',
            'issue_date': 'issue_date',
            'issue_': 'issue_date',
            'date': 'issue_date',
            'year': 'year',
            'grade': 'grade'
        }
        
        # Try to find columns that match our expected fields (case-insensitive)
        flexible_mapping = {}
        for csv_col in csv_columns:
            csv_col_lower = csv_col.lower().strip()
            for expected_col, target_field in column_mapping.items():
                if expected_col.lower() in csv_col_lower or csv_col_lower in expected_col.lower():
                    flexible_mapping[csv_col] = target_field
                    logger.info(f"Mapped '{csv_col}' -> '{target_field}'")
                    break
        
        logger.info(f"Final column mapping: {flexible_mapping}")
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Map the row data to our expected format
                cert_data = {}
                
                # Map columns using flexible mapping
                for csv_col, our_field in flexible_mapping.items():
                    if csv_col in row and row[csv_col].strip():
                        cert_data[our_field] = row[csv_col].strip()
                
                # Also try direct column mapping as fallback
                for csv_col, our_field in column_mapping.items():
                    if csv_col in row and row[csv_col].strip() and our_field not in cert_data:
                        cert_data[our_field] = row[csv_col].strip()
                
                # Handle special cases
                if 'institution_name' in cert_data and 'institution' not in cert_data:
                    cert_data['institution'] = cert_data['institution_name']
                
                # Generate certificate ID if not provided
                if 'certificate_id' not in cert_data:
                    cert_data['certificate_id'] = f"CERT_{generate_secure_token(8)}"
                
                # Set default values
                cert_data.setdefault('issue_date', datetime.now().strftime("%Y-%m-%d"))
                cert_data.setdefault('year', str(datetime.now().year))
                cert_data.setdefault('grade', '')
                cert_data.setdefault('roll_no', '')
                
                # Debug: Log the processed data for first few rows
                if row_num <= 3:
                    logger.info(f"Row {row_num} processed data: {cert_data}")
                    logger.info(f"Row {row_num} raw CSV data: {row}")
                
                # Validate required fields
                required_fields = ['student_name', 'course_name', 'institution']
                missing_fields = [field for field in required_fields if not cert_data.get(field)]
                
                if missing_fields:
                    logger.warning(f"Row {row_num}: Missing required fields: {missing_fields}")
                    logger.warning(f"Row {row_num}: Available data: {list(cert_data.keys())}")
                    continue
                
                certificates_data.append(cert_data)
                
            except Exception as row_error:
                logger.error(f"Error processing row {row_num}: {str(row_error)}")
                continue
        
        if not certificates_data:
            raise HTTPException(status_code=400, detail="No valid certificate data found in CSV")
        
        logger.info(f"Processed {len(certificates_data)} certificates from CSV")
        
        # Call bulk issuance service
        result = await issuance_service.bulk_issue_certificates(certificates_data, institution_id)
        
        return {
            "success": True,
            "message": f"Processed {len(certificates_data)} certificates",
            "results": result
        }
        
    except Exception as e:
        logger.error(f"CSV upload and processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")

# =============================================
# ADMIN DASHBOARD ENDPOINTS
# =============================================

@app.get("/admin/dashboard/stats")
async def get_admin_dashboard_stats():
    """Get comprehensive admin dashboard statistics"""
    try:
        # Get total certificates issued
        total_certificates = supabase_client.client.table("issued_certificates").select("id", count="exact").execute()
        
        # Get verification attempts
        verification_attempts = supabase_client.client.table("verification_logs").select("id", count="exact").execute()
        
        # Get successful verifications
        successful_verifications = supabase_client.client.table("verification_logs").select("id", count="exact").eq("status", "verified").execute()
        
        # Get failed verifications
        failed_verifications = supabase_client.client.table("verification_logs").select("id", count="exact").eq("status", "failed").execute()
        
        # Get recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        recent_certificates = supabase_client.client.table("issued_certificates").select("id", count="exact").gte("created_at", thirty_days_ago).execute()
        
        recent_verifications = supabase_client.client.table("verification_logs").select("id", count="exact").gte("created_at", thirty_days_ago).execute()
        
        # Get institutions count
        institutions = supabase_client.client.table("issued_certificates").select("institution").execute()
        unique_institutions = len(set(cert.get("institution") for cert in institutions.data if cert.get("institution")))
        
        return {
            "total_certificates": total_certificates.count or 0,
            "total_verifications": verification_attempts.count or 0,
            "successful_verifications": successful_verifications.count or 0,
            "failed_verifications": failed_verifications.count or 0,
            "recent_certificates": recent_certificates.count or 0,
            "recent_verifications": recent_verifications.count or 0,
            "unique_institutions": unique_institutions,
            "verification_success_rate": round((successful_verifications.count or 0) / max(verification_attempts.count or 1, 1) * 100, 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to get admin dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/dashboard/recent-activity")
async def get_recent_activity(limit: int = 50):
    """Get recent system activity for admin dashboard"""
    try:
        # Get recent certificate issuances
        recent_certificates = supabase_client.client.table("issued_certificates").select("*").order("created_at", desc=True).limit(limit).execute()
        
        # Get recent verification attempts
        recent_verifications = supabase_client.client.table("verification_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        
        # Combine and sort by date
        activities = []
        
        for cert in recent_certificates.data:
            activities.append({
                "type": "certificate_issued",
                "timestamp": cert.get("created_at"),
                "data": {
                    "certificate_id": cert.get("certificate_id"),
                    "student_name": cert.get("student_name"),
                    "institution": cert.get("institution"),
                    "status": cert.get("status")
                }
            })
        
        for verif in recent_verifications.data:
            activities.append({
                "type": "verification_attempt",
                "timestamp": verif.get("created_at"),
                "data": {
                    "verification_id": verif.get("id"),
                    "status": verif.get("status"),
                    "ip_address": verif.get("ip_address"),
                    "user_agent": verif.get("user_agent")
                }
            })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"activities": activities[:limit]}
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/dashboard/verification-trends")
async def get_verification_trends(days: int = 30):
    """Get verification trends and patterns for fraud detection"""
    try:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get verification data for the period
        verifications = supabase_client.client.table("verification_logs").select("*").gte("created_at", start_date.isoformat()).lte("created_at", end_date.isoformat()).execute()
        
        # Analyze patterns
        daily_stats = {}
        ip_addresses = {}
        user_agents = {}
        failed_attempts = []
        
        for verif in verifications.data:
            date = verif.get("created_at", "")[:10]  # Get date part
            if date not in daily_stats:
                daily_stats[date] = {"total": 0, "successful": 0, "failed": 0}
            
            daily_stats[date]["total"] += 1
            if verif.get("status") == "verified":
                daily_stats[date]["successful"] += 1
            else:
                daily_stats[date]["failed"] += 1
                failed_attempts.append(verif)
            
            # Track IP addresses
            ip = verif.get("ip_address")
            if ip:
                ip_addresses[ip] = ip_addresses.get(ip, 0) + 1
            
            # Track user agents
            ua = verif.get("user_agent")
            if ua:
                user_agents[ua] = user_agents.get(ua, 0) + 1
        
        # Detect suspicious patterns
        suspicious_ips = [ip for ip, count in ip_addresses.items() if count > 10]
        suspicious_agents = [ua for ua, count in user_agents.items() if count > 5]
        
        return {
            "daily_stats": daily_stats,
            "suspicious_ips": suspicious_ips,
            "suspicious_user_agents": suspicious_agents,
            "total_failed_attempts": len(failed_attempts),
            "most_common_ips": sorted(ip_addresses.items(), key=lambda x: x[1], reverse=True)[:10],
            "most_common_user_agents": sorted(user_agents.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
    except Exception as e:
        logger.error(f"Failed to get verification trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/dashboard/institutions")
async def get_institutions_stats():
    """Get statistics by institution"""
    try:
        # Get all certificates grouped by institution
        certificates = supabase_client.client.table("issued_certificates").select("institution, created_at, status").execute()
        
        institution_stats = {}
        for cert in certificates.data:
            inst = cert.get("institution", "Unknown")
            if inst not in institution_stats:
                institution_stats[inst] = {
                    "total_certificates": 0,
                    "recent_certificates": 0,
                    "status_breakdown": {"issued": 0, "verified": 0, "revoked": 0}
                }
            
            institution_stats[inst]["total_certificates"] += 1
            institution_stats[inst]["status_breakdown"][cert.get("status", "issued")] += 1
            
            # Count recent certificates (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            if cert.get("created_at", "") >= thirty_days_ago:
                institution_stats[inst]["recent_certificates"] += 1
        
        return {"institutions": institution_stats}
        
    except Exception as e:
        logger.error(f"Failed to get institutions stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/dashboard/blacklist")
async def get_blacklist():
    """Get blacklisted certificates and IPs"""
    try:
        # Get blacklisted certificates
        blacklisted_certs = supabase_client.client.table("blacklisted_certificates").select("*").execute()
        
        # Get blacklisted IPs
        blacklisted_ips = supabase_client.client.table("blacklisted_ips").select("*").execute()
        
        return {
            "blacklisted_certificates": blacklisted_certs.data,
            "blacklisted_ips": blacklisted_ips.data
        }
        
    except Exception as e:
        logger.error(f"Failed to get blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/dashboard/blacklist-certificate")
async def blacklist_certificate(certificate_id: str, reason: str):
    """Add a certificate to the blacklist"""
    try:
        # Add to blacklist
        result = supabase_client.client.table("blacklisted_certificates").insert({
            "certificate_id": certificate_id,
            "reason": reason,
            "blacklisted_at": datetime.now().isoformat(),
            "blacklisted_by": "admin"
        }).execute()
        
        # Update certificate status
        supabase_client.client.table("issued_certificates").update({
            "status": "blacklisted"
        }).eq("certificate_id", certificate_id).execute()
        
        return {"success": True, "message": f"Certificate {certificate_id} has been blacklisted"}
        
    except Exception as e:
        logger.error(f"Failed to blacklist certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/dashboard/blacklist-ip")
async def blacklist_ip(ip_address: str, reason: str):
    """Add an IP address to the blacklist"""
    try:
        result = supabase_client.client.table("blacklisted_ips").insert({
            "ip_address": ip_address,
            "reason": reason,
            "blacklisted_at": datetime.now().isoformat(),
            "blacklisted_by": "admin"
        }).execute()
        
        return {"success": True, "message": f"IP {ip_address} has been blacklisted"}
        
    except Exception as e:
        logger.error(f"Failed to blacklist IP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# PUBLIC VERIFICATION ENDPOINTS (QR SCANNING)
# =============================================

@app.get("/verify/{attestation_id}")
async def verify_certificate_public(attestation_id: str):
    """Public certificate verification endpoint (Employer workflow)"""
    try:
        result = await public_verification_service.verify_by_attestation_id(attestation_id)
        return result
    except Exception as e:
        logger.error(f"Public verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify/qr")
async def verify_by_qr_data(qr_data: dict):
    """Verify certificate by QR code data"""
    try:
        qr_content = qr_data.get("qr_content")
        if not qr_content:
            raise HTTPException(status_code=400, detail="QR content is required")
        
        result = await public_verification_service.verify_by_qr_data(qr_content)
        return result
    except Exception as e:
        logger.error(f"QR verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verify/{attestation_id}/image")
async def get_verified_certificate_image(attestation_id: str):
    """Get verified certificate image for display"""
    try:
        result = await public_verification_service.get_certificate_image(attestation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Certificate image not found")
        return result
    except Exception as e:
        logger.error(f"Failed to get certificate image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# INSTITUTION MANAGEMENT ENDPOINTS
# =============================================

@app.post("/institutions/register")
async def register_institution(institution_data: dict):
    """Register a new institution"""
    try:
        institution_id = await supabase_client.store_institution(institution_data)
        return {"institution_id": institution_id, "status": "registered"}
    except Exception as e:
        logger.error(f"Institution registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/institutions/{institution_id}/certificates/import")
async def import_certificates(institution_id: str, certificates_data: dict):
    """Import certificates for an institution"""
    try:
        certificates_list = certificates_data.get("certificates", [])
        if not certificates_list:
            raise HTTPException(status_code=400, detail="No certificates data provided")
        
        imported_count = await supabase_client.import_certificates_batch(certificates_list)
        return {"imported_count": imported_count, "status": "success"}
    except Exception as e:
        logger.error(f"Certificate import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ANALYTICS AND REPORTING ENDPOINTS
# =============================================

@app.get("/analytics/verification-stats")
async def get_verification_statistics(institution_id: Optional[str] = None):
    """Get verification statistics"""
    try:
        stats = await public_verification_service.get_verification_statistics(institution_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get verification statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ADDITIONAL FRONTEND ENDPOINTS
# =============================================

@app.get("/reviews")
async def get_reviews(status: Optional[str] = None, search: Optional[str] = None):
    """Get manual review queue"""
    try:
        # Mock data for now
        reviews = [
            {
                "id": "1",
                "name": "John Doe",
                "course": "Computer Science",
                "year": "2023",
                "status": "pending",
                "confidence": 0.75,
                "extracted_data": {
                    "name": "John Doe",
                    "course": "Computer Science",
                    "year": "2023"
                }
            }
        ]
        return {"reviews": reviews}
    except Exception as e:
        logger.error(f"Failed to get reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews/decision")
async def submit_review_decision(decision_data: dict):
    """Submit manual review decision"""
    try:
        # Mock implementation
        return {"success": True, "message": "Review decision submitted"}
    except Exception as e:
        logger.error(f"Failed to submit review decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attestations/{attestation_id}")
async def get_attestation(attestation_id: str):
    """Get attestation details"""
    try:
        # Mock data
        return {
            "id": attestation_id,
            "name": "Sample Student",
            "course": "Computer Science",
            "year": "2023",
            "status": "verified"
        }
    except Exception as e:
        logger.error(f"Failed to get attestation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verifications/{verification_id}")
async def get_verification(verification_id: str):
    """Get verification details"""
    try:
        # Mock data
        return {
            "id": verification_id,
            "valid": True,
            "name": "Sample Student",
            "course": "Computer Science",
            "year": "2023"
        }
    except Exception as e:
        logger.error(f"Failed to get verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-signature")
async def verify_signature(signature_data: dict):
    """Verify digital signature"""
    try:
        # Mock implementation
        return {"valid": True, "message": "Signature verified"}
    except Exception as e:
        logger.error(f"Failed to verify signature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# NEW SYSTEM ENDPOINTS
# =============================================

@app.post("/issue/send-email")
async def send_certificate_email(email_data: dict):
    """Send certificate to student email"""
    try:
        # Mock implementation - in real app, integrate with email service
        certificate_id = email_data.get("certificate_id")
        student_email = email_data.get("student_email")
        
        return {
            "success": True,
            "message": f"Certificate sent to {student_email}",
            "certificate_id": certificate_id
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/certificates")
async def get_student_certificates(student_id: Optional[str] = None):
    """Get certificates for a student"""
    try:
        # Mock data for now
        certificates = [
            {
                "id": "cert_123",
                "student_name": "John Doe",
                "roll_no": "CS2023001",
                "course_name": "Computer Science",
                "year_of_passing": "2023",
                "grade": "A+",
                "institution_name": "University of Technology",
                "image_url": "/api/certificates/cert_123/image",
                "qr_code_url": "/api/certificates/cert_123/qr",
                "pdf_url": "/api/certificates/cert_123/pdf",
                "issued_date": "2023-06-15",
                "status": "verified"
            }
        ]
        return {"certificates": certificates}
    except Exception as e:
        logger.error(f"Failed to get student certificates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/legacy/verify")
async def submit_legacy_verification(file: UploadFile = File(...), verification_data: str = None):
    """Submit legacy certificate for verification"""
    try:
        import json
        
        # Parse verification data
        verify_data = json.loads(verification_data) if verification_data else {}
        
        # Read the uploaded file as bytes
        file_content = await file.read()
        
        # Store verification request (mock implementation)
        request_id = f"req_{generate_secure_token(8)}"
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Legacy verification request submitted successfully"
        }
    except Exception as e:
        logger.error(f"Legacy verification submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/legacy-queue")
async def get_legacy_verification_queue():
    """Get pending legacy verification requests for admin review"""
    try:
        # Mock data for now
        requests = [
            {
                "id": "legacy_001",
                "student_name": "Jane Smith",
                "roll_no": "CS2022001",
                "course_name": "Computer Science",
                "year_of_passing": "2022",
                "email": "jane.smith@email.com",
                "phone": "+1234567890",
                "image_url": "/api/legacy/legacy_001/image",
                "submitted_at": "2023-12-01T10:30:00Z",
                "status": "pending"
            }
        ]
        return {"requests": requests}
    except Exception as e:
        logger.error(f"Failed to get legacy queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/legacy/approve")
async def approve_legacy_certificate(approval_data: dict):
    """Approve a legacy certificate verification"""
    try:
        request_id = approval_data.get("request_id")
        admin_notes = approval_data.get("admin_notes", "")
        
        # Mock implementation
        return {
            "success": True,
            "message": "Legacy certificate approved and QR code generated",
            "request_id": request_id,
            "certificate_id": f"cert_{request_id}"
        }
    except Exception as e:
        logger.error(f"Failed to approve legacy certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/legacy/reject")
async def reject_legacy_certificate(rejection_data: dict):
    """Reject a legacy certificate verification"""
    try:
        request_id = rejection_data.get("request_id")
        rejection_reason = rejection_data.get("rejection_reason", "")
        
        # Mock implementation
        return {
            "success": True,
            "message": "Legacy certificate verification rejected",
            "request_id": request_id
        }
    except Exception as e:
        logger.error(f"Failed to reject legacy certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
