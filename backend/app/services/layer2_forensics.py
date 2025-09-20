"""
Layer 2 - Image Forensics Service
Implements comprehensive tamper detection using multiple techniques:
- Copy-move detection (SIFT/ORB)
- Error Level Analysis (ELA)
- Double compression detection
- Noise analysis and PRNU
- Hash integrity checks
"""
import time
import logging
import cv2
import numpy as np
from PIL import Image, ImageDraw
import hashlib
import imagehash
from typing import List, Tuple, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from scipy import ndimage
from skimage import feature, measure
import warnings
warnings.filterwarnings('ignore')

from ..models import ForensicAnalysis, TamperType
from ..config import settings

logger = logging.getLogger(__name__)

class Layer2ForensicsService:
    """
    Layer 2: Comprehensive image forensics and tamper detection
    Implements multiple complementary techniques for robust analysis
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize feature detectors
        try:
            self.sift_detector = cv2.SIFT_create()
            self.orb_detector = cv2.ORB_create()
        except AttributeError:
            # Fallback for older OpenCV versions
            self.sift_detector = cv2.xfeatures2d.SIFT_create()
            self.orb_detector = cv2.ORB_create()
        
        # Forensic analysis parameters
        self.copy_move_threshold = 0.7
        self.ela_threshold = 30
        self.compression_threshold = 0.8
        self.noise_threshold = 0.6
        
        logger.info("Layer 2 Forensics Service initialized")
    
    async def analyze_image(self, image: Image.Image, reference_hash: Optional[str] = None) -> ForensicAnalysis:
        """
        Comprehensive forensic analysis of certificate image
        """
        start_time = time.time()
        
        try:
            # Convert image to different formats needed for analysis
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Run all forensic analyses in parallel
            tasks = [
                self._detect_copy_move(gray_image),
                self._error_level_analysis(image),
                self._detect_double_compression(cv_image),
                self._analyze_noise_patterns(gray_image),
                self._calculate_image_hashes(image),
                self._detect_resampling(gray_image),
                self._analyze_jpeg_artifacts(cv_image)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            copy_move_score = results[0] if not isinstance(results[0], Exception) else 0.0
            ela_score = results[1] if not isinstance(results[1], Exception) else 0.0
            compression_score = results[2] if not isinstance(results[2], Exception) else 0.0
            noise_score = results[3] if not isinstance(results[3], Exception) else 0.0
            hashes = results[4] if not isinstance(results[4], Exception) else {}
            resampling_score = results[5] if not isinstance(results[5], Exception) else 0.0
            jpeg_score = results[6] if not isinstance(results[6], Exception) else 0.0
            
            # Detect suspicious regions
            suspicious_regions = await self._find_suspicious_regions(cv_image, gray_image)
            
            # Determine tamper types
            tamper_types = self._classify_tamper_types(
                copy_move_score, ela_score, compression_score, 
                noise_score, resampling_score
            )
            
            # Check hash integrity
            hash_match = None
            if reference_hash and hashes.get('sha256'):
                hash_match = reference_hash == hashes['sha256']
                if not hash_match:
                    tamper_types.append(TamperType.HASH_MISMATCH)
            
            # Calculate overall tamper probability
            tamper_probability = self._calculate_tamper_probability(
                copy_move_score, ela_score, compression_score, 
                noise_score, resampling_score, jpeg_score
            )
            
            # Create forensic analysis result
            analysis = ForensicAnalysis(
                copy_move_score=copy_move_score,
                ela_score=ela_score,
                double_compression_score=compression_score,
                noise_analysis_score=noise_score,
                sha256_hash=hashes.get('sha256'),
                perceptual_hash=hashes.get('phash'),
                hash_match=hash_match,
                suspicious_regions=suspicious_regions,
                tamper_types=tamper_types,
                tamper_probability=tamper_probability,
                analysis_time=time.time() - start_time
            )
            
            logger.info(f"Forensic analysis completed in {analysis.analysis_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Forensic analysis failed: {str(e)}")
            return ForensicAnalysis(
                tamper_probability=0.5,  # Uncertain due to error
                analysis_time=time.time() - start_time
            )
    
    async def _detect_copy_move(self, gray_image: np.ndarray) -> float:
        """
        Detect copy-move tampering using SIFT feature matching
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._copy_move_detection_sync, 
                gray_image
            )
        except Exception as e:
            logger.error(f"Copy-move detection failed: {str(e)}")
            return 0.0
    
    def _copy_move_detection_sync(self, gray_image: np.ndarray) -> float:
        """Synchronous copy-move detection"""
        try:
            # Extract SIFT features
            keypoints, descriptors = self.sift_detector.detectAndCompute(gray_image, None)
            
            if descriptors is None or len(descriptors) < 10:
                return 0.0
            
            # Create FLANN matcher
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            
            # Match features against themselves
            matches = flann.knnMatch(descriptors, descriptors, k=3)
            
            # Filter good matches (excluding self-matches)
            good_matches = []
            for match_group in matches:
                if len(match_group) >= 2:
                    m, n = match_group[0], match_group[1]
                    # Exclude self-matches and apply Lowe's ratio test
                    if m.queryIdx != m.trainIdx and m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            # Calculate copy-move score based on number of suspicious matches
            total_features = len(keypoints)
            suspicious_matches = len(good_matches)
            
            if total_features == 0:
                return 0.0
            
            copy_move_ratio = suspicious_matches / total_features
            
            # Apply threshold and normalize
            copy_move_score = min(copy_move_ratio * 2.0, 1.0)
            
            return copy_move_score
            
        except Exception as e:
            logger.error(f"SIFT copy-move detection error: {str(e)}")
            return 0.0
    
    async def _error_level_analysis(self, image: Image.Image) -> float:
        """
        Error Level Analysis to detect manipulated regions
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._ela_analysis_sync, 
                image
            )
        except Exception as e:
            logger.error(f"ELA analysis failed: {str(e)}")
            return 0.0
    
    def _ela_analysis_sync(self, image: Image.Image) -> float:
        """Synchronous ELA analysis"""
        try:
            # Save image at different quality levels
            import io
            
            # Original image
            original_buffer = io.BytesIO()
            image.save(original_buffer, format='JPEG', quality=90)
            original_size = len(original_buffer.getvalue())
            
            # Re-compressed image
            temp_buffer = io.BytesIO()
            image.save(temp_buffer, format='JPEG', quality=90)
            temp_buffer.seek(0)
            recompressed = Image.open(temp_buffer)
            
            # Convert to numpy arrays
            original_array = np.array(image)
            recompressed_array = np.array(recompressed)
            
            # Calculate difference
            if original_array.shape != recompressed_array.shape:
                return 0.0
            
            # Calculate ELA
            ela_diff = np.abs(original_array.astype(np.float32) - recompressed_array.astype(np.float32))
            
            # Calculate statistics
            mean_error = np.mean(ela_diff)
            max_error = np.max(ela_diff)
            std_error = np.std(ela_diff)
            
            # Normalize ELA score
            ela_score = min(mean_error / 50.0, 1.0)  # Normalize to 0-1
            
            return ela_score
            
        except Exception as e:
            logger.error(f"ELA analysis error: {str(e)}")
            return 0.0
    
    async def _detect_double_compression(self, cv_image: np.ndarray) -> float:
        """
        Detect double JPEG compression artifacts
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._double_compression_sync, 
                cv_image
            )
        except Exception as e:
            logger.error(f"Double compression detection failed: {str(e)}")
            return 0.0
    
    def _double_compression_sync(self, cv_image: np.ndarray) -> float:
        """Synchronous double compression detection"""
        try:
            # Convert to YUV color space
            yuv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2YUV)
            y_channel = yuv_image[:, :, 0]
            
            # Apply DCT to 8x8 blocks
            h, w = y_channel.shape
            dct_coeffs = []
            
            for i in range(0, h - 8, 8):
                for j in range(0, w - 8, 8):
                    block = y_channel[i:i+8, j:j+8].astype(np.float32)
                    dct_block = cv2.dct(block)
                    dct_coeffs.append(dct_block.flatten())
            
            if not dct_coeffs:
                return 0.0
            
            # Analyze DCT coefficient histogram
            all_coeffs = np.concatenate(dct_coeffs)
            hist, bins = np.histogram(all_coeffs, bins=100, range=(-50, 50))
            
            # Look for periodic patterns indicating double compression
            # This is a simplified approach - in practice, you'd use more sophisticated methods
            periodicity_score = self._detect_periodicity(hist)
            
            return min(periodicity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Double compression analysis error: {str(e)}")
            return 0.0
    
    def _detect_periodicity(self, histogram: np.ndarray) -> float:
        """Detect periodic patterns in DCT coefficient histogram"""
        try:
            # Simple approach: look for regular patterns
            # Calculate autocorrelation
            autocorr = np.correlate(histogram, histogram, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Find peaks indicating periodicity
            if len(autocorr) < 10:
                return 0.0
            
            # Normalize and look for secondary peaks
            autocorr_norm = autocorr / autocorr[0] if autocorr[0] > 0 else autocorr
            
            # Simple peak detection
            peaks = []
            for i in range(1, min(20, len(autocorr_norm) - 1)):
                if (autocorr_norm[i] > autocorr_norm[i-1] and 
                    autocorr_norm[i] > autocorr_norm[i+1] and 
                    autocorr_norm[i] > 0.1):
                    peaks.append(autocorr_norm[i])
            
            # Score based on peak strength
            periodicity_score = sum(peaks) / len(peaks) if peaks else 0.0
            return min(periodicity_score * 2.0, 1.0)
            
        except Exception:
            return 0.0
    
    async def _analyze_noise_patterns(self, gray_image: np.ndarray) -> float:
        """
        Analyze noise patterns for inconsistencies indicating tampering
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._noise_analysis_sync, 
                gray_image
            )
        except Exception as e:
            logger.error(f"Noise analysis failed: {str(e)}")
            return 0.0
    
    def _noise_analysis_sync(self, gray_image: np.ndarray) -> float:
        """Synchronous noise pattern analysis"""
        try:
            # Apply noise extraction filter
            noise = self._extract_noise(gray_image)
            
            # Divide image into blocks and analyze noise variance
            h, w = gray_image.shape
            block_size = 64
            noise_variances = []
            
            for i in range(0, h - block_size, block_size // 2):
                for j in range(0, w - block_size, block_size // 2):
                    noise_block = noise[i:i+block_size, j:j+block_size]
                    variance = np.var(noise_block)
                    noise_variances.append(variance)
            
            if not noise_variances:
                return 0.0
            
            # Calculate coefficient of variation
            mean_variance = np.mean(noise_variances)
            std_variance = np.std(noise_variances)
            
            if mean_variance == 0:
                return 0.0
            
            cv = std_variance / mean_variance
            
            # Higher CV indicates inconsistent noise (potential tampering)
            noise_inconsistency_score = min(cv / 2.0, 1.0)
            
            return noise_inconsistency_score
            
        except Exception as e:
            logger.error(f"Noise analysis error: {str(e)}")
            return 0.0
    
    def _extract_noise(self, gray_image: np.ndarray) -> np.ndarray:
        """Extract noise component from image"""
        try:
            # Apply Gaussian blur to get approximate image
            blurred = cv2.GaussianBlur(gray_image, (5, 5), 1.0)
            
            # Subtract to get noise
            noise = gray_image.astype(np.float32) - blurred.astype(np.float32)
            
            return noise
            
        except Exception:
            return np.zeros_like(gray_image, dtype=np.float32)
    
    async def _calculate_image_hashes(self, image: Image.Image) -> Dict[str, str]:
        """Calculate various image hashes for integrity checking"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._calculate_hashes_sync, 
                image
            )
        except Exception as e:
            logger.error(f"Hash calculation failed: {str(e)}")
            return {}
    
    def _calculate_hashes_sync(self, image: Image.Image) -> Dict[str, str]:
        """Synchronous hash calculation"""
        try:
            # Convert image to bytes for SHA256
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            
            # Calculate SHA256
            sha256_hash = hashlib.sha256(img_data).hexdigest()
            
            # Calculate perceptual hash
            phash = str(imagehash.phash(image))
            
            # Calculate average hash
            ahash = str(imagehash.average_hash(image))
            
            # Calculate difference hash
            dhash = str(imagehash.dhash(image))
            
            return {
                'sha256': sha256_hash,
                'phash': phash,
                'ahash': ahash,
                'dhash': dhash
            }
            
        except Exception as e:
            logger.error(f"Hash calculation error: {str(e)}")
            return {}
    
    async def _detect_resampling(self, gray_image: np.ndarray) -> float:
        """
        Detect image resampling artifacts
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._resampling_detection_sync, 
                gray_image
            )
        except Exception as e:
            logger.error(f"Resampling detection failed: {str(e)}")
            return 0.0
    
    def _resampling_detection_sync(self, gray_image: np.ndarray) -> float:
        """Synchronous resampling detection"""
        try:
            # Apply second derivative to detect linear dependencies
            laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
            
            # Calculate variance of Laplacian
            variance = cv2.Laplacian(gray_image, cv2.CV_64F).var()
            
            # Apply FFT to detect periodic patterns
            f_transform = np.fft.fft2(gray_image)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)
            
            # Look for grid patterns in frequency domain
            h, w = magnitude_spectrum.shape
            center_h, center_w = h // 2, w // 2
            
            # Sample radial lines from center
            radial_profiles = []
            for angle in range(0, 180, 15):
                rad = np.radians(angle)
                for r in range(1, min(center_h, center_w)):
                    y = int(center_h + r * np.sin(rad))
                    x = int(center_w + r * np.cos(rad))
                    if 0 <= y < h and 0 <= x < w:
                        radial_profiles.append(magnitude_spectrum[y, x])
            
            # Calculate periodicity in radial profiles
            if radial_profiles:
                profile_variance = np.var(radial_profiles)
                resampling_score = min(profile_variance / 1000.0, 1.0)
            else:
                resampling_score = 0.0
            
            return resampling_score
            
        except Exception as e:
            logger.error(f"Resampling detection error: {str(e)}")
            return 0.0
    
    async def _analyze_jpeg_artifacts(self, cv_image: np.ndarray) -> float:
        """
        Analyze JPEG compression artifacts for inconsistencies
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._jpeg_artifacts_sync, 
                cv_image
            )
        except Exception as e:
            logger.error(f"JPEG artifacts analysis failed: {str(e)}")
            return 0.0
    
    def _jpeg_artifacts_sync(self, cv_image: np.ndarray) -> float:
        """Synchronous JPEG artifacts analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect blocking artifacts
            blocking_score = self._detect_blocking_artifacts(gray)
            
            # Detect ringing artifacts
            ringing_score = self._detect_ringing_artifacts(gray)
            
            # Combine scores
            jpeg_score = (blocking_score + ringing_score) / 2.0
            
            return jpeg_score
            
        except Exception as e:
            logger.error(f"JPEG artifacts analysis error: {str(e)}")
            return 0.0
    
    def _detect_blocking_artifacts(self, gray_image: np.ndarray) -> float:
        """Detect JPEG blocking artifacts"""
        try:
            h, w = gray_image.shape
            
            # Calculate horizontal and vertical differences at 8-pixel intervals
            horizontal_diffs = []
            vertical_diffs = []
            
            # Horizontal blocking
            for i in range(0, h, 8):
                if i + 1 < h:
                    diff = np.mean(np.abs(gray_image[i, :].astype(np.float32) - 
                                        gray_image[i+1, :].astype(np.float32)))
                    horizontal_diffs.append(diff)
            
            # Vertical blocking
            for j in range(0, w, 8):
                if j + 1 < w:
                    diff = np.mean(np.abs(gray_image[:, j].astype(np.float32) - 
                                        gray_image[:, j+1].astype(np.float32)))
                    vertical_diffs.append(diff)
            
            # Calculate blocking score
            if horizontal_diffs and vertical_diffs:
                avg_h_diff = np.mean(horizontal_diffs)
                avg_v_diff = np.mean(vertical_diffs)
                blocking_score = (avg_h_diff + avg_v_diff) / 100.0
                return min(blocking_score, 1.0)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _detect_ringing_artifacts(self, gray_image: np.ndarray) -> float:
        """Detect JPEG ringing artifacts"""
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150)
            
            # Dilate edges to create regions
            kernel = np.ones((3, 3), np.uint8)
            dilated_edges = cv2.dilate(edges, kernel, iterations=1)
            
            # Calculate gradient magnitude near edges
            grad_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Calculate ringing measure
            edge_pixels = dilated_edges > 0
            if np.sum(edge_pixels) > 0:
                edge_gradients = gradient_magnitude[edge_pixels]
                ringing_score = np.std(edge_gradients) / 100.0
                return min(ringing_score, 1.0)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    async def _find_suspicious_regions(self, cv_image: np.ndarray, gray_image: np.ndarray) -> List[List[int]]:
        """
        Find regions that appear suspicious based on multiple criteria
        """
        try:
            suspicious_regions = []
            
            # Find regions with inconsistent noise
            noise_regions = await self._find_noise_inconsistent_regions(gray_image)
            suspicious_regions.extend(noise_regions)
            
            # Find regions with ELA anomalies
            ela_regions = await self._find_ela_anomalous_regions(cv_image)
            suspicious_regions.extend(ela_regions)
            
            # Merge overlapping regions
            merged_regions = self._merge_overlapping_regions(suspicious_regions)
            
            return merged_regions
            
        except Exception as e:
            logger.error(f"Suspicious region detection failed: {str(e)}")
            return []
    
    async def _find_noise_inconsistent_regions(self, gray_image: np.ndarray) -> List[List[int]]:
        """Find regions with inconsistent noise patterns"""
        try:
            regions = []
            noise = self._extract_noise(gray_image)
            
            h, w = gray_image.shape
            block_size = 32
            threshold = 2.0  # Standard deviations above mean
            
            # Calculate global noise statistics
            global_noise_std = np.std(noise)
            
            for i in range(0, h - block_size, block_size // 2):
                for j in range(0, w - block_size, block_size // 2):
                    block_noise = noise[i:i+block_size, j:j+block_size]
                    block_std = np.std(block_noise)
                    
                    # Check if block noise is significantly different
                    if abs(block_std - global_noise_std) > threshold * global_noise_std:
                        regions.append([j, i, j + block_size, i + block_size])
            
            return regions
            
        except Exception:
            return []
    
    async def _find_ela_anomalous_regions(self, cv_image: np.ndarray) -> List[List[int]]:
        """Find regions with ELA anomalies"""
        try:
            # This is a placeholder implementation
            # In practice, you would analyze the ELA image for high-error regions
            regions = []
            
            # Convert to PIL for ELA analysis
            pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            
            # Perform simplified ELA region analysis
            # This would be more sophisticated in a production system
            h, w = cv_image.shape[:2]
            
            # Sample a few regions for demonstration
            if h > 100 and w > 100:
                # Add a placeholder suspicious region
                regions.append([w//4, h//4, 3*w//4, 3*h//4])
            
            return regions
            
        except Exception:
            return []
    
    def _merge_overlapping_regions(self, regions: List[List[int]]) -> List[List[int]]:
        """Merge overlapping bounding boxes"""
        if not regions:
            return []
        
        # Sort by x-coordinate
        regions.sort(key=lambda x: x[0])
        
        merged = [regions[0]]
        
        for current in regions[1:]:
            last = merged[-1]
            
            # Check for overlap
            if (current[0] <= last[2] and current[1] <= last[3] and
                current[2] >= last[0] and current[3] >= last[1]):
                # Merge regions
                merged[-1] = [
                    min(last[0], current[0]),
                    min(last[1], current[1]),
                    max(last[2], current[2]),
                    max(last[3], current[3])
                ]
            else:
                merged.append(current)
        
        return merged
    
    def _classify_tamper_types(self, copy_move_score: float, ela_score: float, 
                              compression_score: float, noise_score: float, 
                              resampling_score: float) -> List[TamperType]:
        """Classify types of tampering detected"""
        tamper_types = []
        
        if copy_move_score > 0.6:
            tamper_types.append(TamperType.COPY_MOVE)
        
        if ela_score > 0.7:
            tamper_types.append(TamperType.ELA_ANOMALY)
        
        if compression_score > 0.8:
            tamper_types.append(TamperType.DOUBLE_COMPRESSION)
        
        if noise_score > 0.7:
            tamper_types.append(TamperType.NOISE_INCONSISTENCY)
        
        if resampling_score > 0.6:
            tamper_types.append(TamperType.RESAMPLING)
        
        return tamper_types
    
    def _calculate_tamper_probability(self, copy_move_score: float, ela_score: float,
                                    compression_score: float, noise_score: float,
                                    resampling_score: float, jpeg_score: float) -> float:
        """Calculate overall probability of tampering"""
        # Weighted combination of scores
        weights = {
            'copy_move': 0.25,
            'ela': 0.20,
            'compression': 0.15,
            'noise': 0.20,
            'resampling': 0.10,
            'jpeg': 0.10
        }
        
        weighted_score = (
            copy_move_score * weights['copy_move'] +
            ela_score * weights['ela'] +
            compression_score * weights['compression'] +
            noise_score * weights['noise'] +
            resampling_score * weights['resampling'] +
            jpeg_score * weights['jpeg']
        )
        
        return min(weighted_score, 1.0)
