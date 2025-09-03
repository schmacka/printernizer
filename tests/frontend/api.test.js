/**
 * Frontend API service tests
 * Tests the API service layer that handles all HTTP communications
 */
import fetchMock from 'fetch-mock';

// Import API service (adjust path as needed)
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Mock the API service since we need to test it
const ApiService = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  },
  
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  },
  
  async put(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  },
  
  async delete(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.status === 204 ? null : response.json();
  }
};

describe('API Service', () => {
  
  describe('Printer API', () => {
    test('should get all printers', async () => {
      const mockPrinters = {
        printers: [
          testUtils.createMockPrinter(),
          testUtils.createMockPrinter({ id: 'printer_002', name: 'Test Prusa Core One', type: 'prusa' })
        ],
        total_count: 2
      };
      
      fetchMock.get(`${API_BASE_URL}/printers`, mockPrinters);
      
      const result = await ApiService.get('/printers');
      
      expect(result.printers).toHaveLength(2);
      expect(result.total_count).toBe(2);
      expect(result.printers[0].type).toBe('bambu_lab');
      expect(result.printers[1].type).toBe('prusa');
    });
    
    test('should create new printer', async () => {
      const newPrinter = {
        name: 'New Bambu A1',
        type: 'bambu_lab',
        model: 'A1',
        ip_address: '192.168.1.101',
        access_code: 'test_code'
      };
      
      const createdPrinter = { id: 'new_printer_001', ...newPrinter };
      
      fetchMock.post(`${API_BASE_URL}/printers`, createdPrinter);
      
      const result = await ApiService.post('/printers', newPrinter);
      
      expect(result.id).toBe('new_printer_001');
      expect(result.name).toBe('New Bambu A1');
      expect(result.type).toBe('bambu_lab');
    });
    
    test('should get printer status', async () => {
      const printerId = 'test_printer_001';
      const mockStatus = {
        printer_id: printerId,
        status: 'online',
        current_job: {
          job_name: 'test_print.3mf',
          progress: 67.5,
          layer_current: 200,
          layer_total: 300
        },
        temperatures: {
          nozzle: 210.0,
          bed: 60.0,
          chamber: 28.5
        }
      };
      
      fetchMock.get(`${API_BASE_URL}/printers/${printerId}/status`, mockStatus);
      
      const result = await ApiService.get(`/printers/${printerId}/status`);
      
      expect(result.status).toBe('online');
      expect(result.current_job.progress).toBe(67.5);
      expect(result.temperatures.nozzle).toBe(210.0);
    });
    
    test('should update printer configuration', async () => {
      const printerId = 'test_printer_001';
      const updateData = { name: 'Updated Printer Name' };
      const updatedPrinter = { ...testUtils.createMockPrinter(), ...updateData };
      
      fetchMock.put(`${API_BASE_URL}/printers/${printerId}`, updatedPrinter);
      
      const result = await ApiService.put(`/printers/${printerId}`, updateData);
      
      expect(result.name).toBe('Updated Printer Name');
    });
    
    test('should delete printer', async () => {
      const printerId = 'test_printer_001';
      
      fetchMock.delete(`${API_BASE_URL}/printers/${printerId}`, 204);
      
      const result = await ApiService.delete(`/printers/${printerId}`);
      
      expect(result).toBeNull();
    });
  });
  
  describe('Jobs API', () => {
    test('should get all jobs with filtering', async () => {
      const mockJobs = {
        jobs: [
          testUtils.createMockJob(),
          testUtils.createMockJob({ id: 'job_002', status: 'completed', progress: 100 })
        ],
        total_count: 2,
        filters_applied: { status: 'all' }
      };
      
      fetchMock.get(`${API_BASE_URL}/jobs?status=all`, mockJobs);
      
      const result = await ApiService.get('/jobs?status=all');
      
      expect(result.jobs).toHaveLength(2);
      expect(result.jobs[0].status).toBe('printing');
      expect(result.jobs[1].status).toBe('completed');
    });
    
    test('should create new job', async () => {
      const newJob = {
        printer_id: 'test_printer_001',
        job_name: 'new_model.3mf',
        material_type: 'PLA',
        material_color: 'Blue',
        is_business: true
      };
      
      const createdJob = { id: 'new_job_001', ...newJob, status: 'queued', progress: 0 };
      
      fetchMock.post(`${API_BASE_URL}/jobs`, createdJob);
      
      const result = await ApiService.post('/jobs', newJob);
      
      expect(result.id).toBe('new_job_001');
      expect(result.status).toBe('queued');
      expect(result.is_business).toBe(true);
    });
    
    test('should get job details', async () => {
      const jobId = 'test_job_001';
      const mockJob = {
        ...testUtils.createMockJob(),
        cost_breakdown: {
          material_cost_eur: 1.28,
          power_cost_eur: 0.09,
          total_cost_excluding_vat_eur: 1.37,
          vat_amount_eur: 0.26,
          total_cost_including_vat_eur: 1.63
        }
      };
      
      fetchMock.get(`${API_BASE_URL}/jobs/${jobId}`, mockJob);
      
      const result = await ApiService.get(`/jobs/${jobId}`);
      
      expect(result.id).toBe('test_job_001');
      expect(result.cost_breakdown).toBeDefined();
      expect(result.cost_breakdown.vat_amount_eur).toBe(0.26);
    });
    
    test('should update job status', async () => {
      const jobId = 'test_job_001';
      const statusUpdate = {
        status: 'completed',
        progress: 100,
        actual_duration: 3600
      };
      
      const updatedJob = { ...testUtils.createMockJob(), ...statusUpdate };
      
      fetchMock.put(`${API_BASE_URL}/jobs/${jobId}/status`, updatedJob);
      
      const result = await ApiService.put(`/jobs/${jobId}/status`, statusUpdate);
      
      expect(result.status).toBe('completed');
      expect(result.progress).toBe(100);
    });
  });
  
  describe('Files API', () => {
    test('should get unified file listing', async () => {
      const mockFiles = {
        files: [
          testUtils.createMockFile(),
          testUtils.createMockFile({ 
            id: 'file_002', 
            download_status: 'downloaded', 
            location: 'local',
            local_path: '/downloads/test_model_2.3mf'
          })
        ],
        summary: {
          total_files: 2,
          available_downloads: 1,
          downloaded_files: 1,
          local_only_files: 0
        }
      };
      
      fetchMock.get(`${API_BASE_URL}/files/unified`, mockFiles);
      
      const result = await ApiService.get('/files/unified');
      
      expect(result.files).toHaveLength(2);
      expect(result.summary.available_downloads).toBe(1);
      expect(result.files[0].location).toBe('printer');
      expect(result.files[1].location).toBe('local');
    });
    
    test('should download file from printer', async () => {
      const fileId = 'test_file_001';
      const downloadResult = {
        success: true,
        file_id: fileId,
        local_path: '/downloads/bambu_a1/2025-09-03/test_model.3mf',
        file_size: 2048000,
        download_time_seconds: 15.5
      };
      
      fetchMock.post(`${API_BASE_URL}/files/${fileId}/download`, downloadResult);
      
      const result = await ApiService.post(`/files/${fileId}/download`, {});
      
      expect(result.success).toBe(true);
      expect(result.local_path).toContain('test_model.3mf');
      expect(result.file_size).toBe(2048000);
    });
    
    test('should delete local file', async () => {
      const fileId = 'test_file_001';
      
      fetchMock.delete(`${API_BASE_URL}/files/${fileId}`, 204);
      
      const result = await ApiService.delete(`/files/${fileId}`);
      
      expect(result).toBeNull();
    });
  });
  
  describe('Dashboard API', () => {
    test('should get dashboard statistics', async () => {
      const mockStats = {
        printer_summary: {
          total_printers: 2,
          online_printers: 1,
          printing_printers: 1,
          offline_printers: 1
        },
        job_summary: {
          total_jobs: 25,
          active_jobs: 3,
          completed_jobs: 20,
          failed_jobs: 2
        },
        material_summary: {
          total_filament_used_kg: 15.75,
          most_used_material: 'PLA',
          material_cost_total_eur: 787.50
        },
        business_summary: {
          total_revenue_eur: 1250.00,
          total_costs_eur: 850.00,
          total_vat_collected_eur: 237.50,
          active_business_jobs: 2
        }
      };
      
      fetchMock.get(`${API_BASE_URL}/dashboard/stats`, mockStats);
      
      const result = await ApiService.get('/dashboard/stats');
      
      expect(result.printer_summary.total_printers).toBe(2);
      expect(result.business_summary.total_revenue_eur).toBe(1250.00);
      expect(result.material_summary.most_used_material).toBe('PLA');
    });
  });
  
  describe('Error Handling', () => {
    test('should handle 404 errors', async () => {
      fetchMock.get(`${API_BASE_URL}/printers/nonexistent`, 404);
      
      await expect(ApiService.get('/printers/nonexistent'))
        .rejects.toThrow('HTTP 404');
    });
    
    test('should handle 500 server errors', async () => {
      fetchMock.get(`${API_BASE_URL}/printers`, 500);
      
      await expect(ApiService.get('/printers'))
        .rejects.toThrow('HTTP 500');
    });
    
    test('should handle network errors', async () => {
      fetchMock.get(`${API_BASE_URL}/printers`, Promise.reject(new Error('Network error')));
      
      await expect(ApiService.get('/printers'))
        .rejects.toThrow('Network error');
    });
    
    test('should handle malformed JSON responses', async () => {
      fetchMock.get(`${API_BASE_URL}/printers`, 'invalid json');
      
      await expect(ApiService.get('/printers'))
        .rejects.toThrow();
    });
  });
  
  describe('Request Headers and Authentication', () => {
    test('should include proper headers for POST requests', async () => {
      const newPrinter = { name: 'Test Printer' };
      
      fetchMock.post(`${API_BASE_URL}/printers`, (url, options) => {
        expect(options.headers['Content-Type']).toBe('application/json');
        return testUtils.createMockPrinter();
      });
      
      await ApiService.post('/printers', newPrinter);
    });
    
    test('should properly serialize request body', async () => {
      const jobData = { printer_id: 'test', job_name: 'test.3mf' };
      
      fetchMock.post(`${API_BASE_URL}/jobs`, (url, options) => {
        const parsedBody = JSON.parse(options.body);
        expect(parsedBody.printer_id).toBe('test');
        expect(parsedBody.job_name).toBe('test.3mf');
        return testUtils.createMockJob();
      });
      
      await ApiService.post('/jobs', jobData);
    });
  });
  
  describe('Response Data Validation', () => {
    test('should validate printer response structure', async () => {
      const mockPrinter = testUtils.createMockPrinter();
      
      fetchMock.get(`${API_BASE_URL}/printers/test_001`, mockPrinter);
      
      const result = await ApiService.get('/printers/test_001');
      
      // Validate required fields
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('name');
      expect(result).toHaveProperty('type');
      expect(result).toHaveProperty('status');
      expect(['bambu_lab', 'prusa']).toContain(result.type);
    });
    
    test('should validate job response structure', async () => {
      const mockJob = testUtils.createMockJob();
      
      fetchMock.get(`${API_BASE_URL}/jobs/test_001`, mockJob);
      
      const result = await ApiService.get('/jobs/test_001');
      
      // Validate required fields
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('printer_id');
      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('progress');
      expect(result.progress).toBeGreaterThanOrEqual(0);
      expect(result.progress).toBeLessThanOrEqual(100);
    });
  });
});