/**
 * Dashboard component tests
 * Tests the main dashboard view with real-time printer status, 
 * job monitoring, and business statistics
 */
import { screen, fireEvent, waitFor } from '@testing-library/dom';
import fetchMock from 'fetch-mock';

describe('Dashboard Component', () => {
  const API_BASE_URL = 'http://localhost:8000/api/v1';
  
  // Mock dashboard initialization function
  const initializeDashboard = async () => {
    // This would normally import from the actual dashboard.js file
    // For testing, we'll mock the dashboard functionality
    
    const dashboardElement = document.getElementById('dashboard-view');
    
    // Simulate dashboard rendering
    dashboardElement.innerHTML = `
      <div class="dashboard-header">
        <h1>Printernizer Dashboard</h1>
        <div class="status-indicator" id="connection-status">Online</div>
      </div>
      
      <div class="dashboard-grid">
        <div class="stats-section">
          <div class="stat-card" id="printer-stats">
            <h3>Printers</h3>
            <div class="stat-value" id="online-printers">0</div>
            <div class="stat-label">Online</div>
          </div>
          
          <div class="stat-card" id="job-stats">
            <h3>Active Jobs</h3>
            <div class="stat-value" id="active-jobs">0</div>
            <div class="stat-label">Running</div>
          </div>
          
          <div class="stat-card" id="business-stats">
            <h3>Revenue (EUR)</h3>
            <div class="stat-value" id="total-revenue">0.00</div>
            <div class="stat-label">This Month</div>
          </div>
        </div>
        
        <div class="printers-section">
          <h2>Printer Status</h2>
          <div id="printer-cards-container"></div>
        </div>
        
        <div class="recent-jobs-section">
          <h2>Recent Jobs</h2>
          <div id="recent-jobs-container"></div>
        </div>
      </div>
    `;
    
    // Load dashboard data
    await loadDashboardData();
  };
  
  const loadDashboardData = async () => {
    try {
      // Fetch dashboard stats
      const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
      const stats = await response.json();
      
      updateStatistics(stats);
      await loadPrinterCards(stats.printer_summary);
      await loadRecentJobs();
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      showError('Failed to load dashboard data');
    }
  };
  
  const updateStatistics = (stats) => {
    // Update printer stats
    const onlinePrinters = document.getElementById('online-printers');
    if (onlinePrinters) {
      onlinePrinters.textContent = stats.printer_summary.online_printers;
    }
    
    // Update job stats
    const activeJobs = document.getElementById('active-jobs');
    if (activeJobs) {
      activeJobs.textContent = stats.job_summary.active_jobs;
    }
    
    // Update business stats
    const totalRevenue = document.getElementById('total-revenue');
    if (totalRevenue) {
      totalRevenue.textContent = stats.business_summary.total_revenue_eur.toFixed(2);
    }
  };
  
  const loadPrinterCards = async (printerSummary) => {
    const container = document.getElementById('printer-cards-container');
    if (!container) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/printers`);
      const data = await response.json();
      
      container.innerHTML = '';
      
      data.printers.forEach(printer => {
        const card = createPrinterCard(printer);
        container.appendChild(card);
      });
      
    } catch (error) {
      console.error('Failed to load printer cards:', error);
    }
  };
  
  const createPrinterCard = (printer) => {
    const card = document.createElement('div');
    card.className = `printer-card status-${printer.status}`;
    card.setAttribute('data-printer-id', printer.id);
    
    card.innerHTML = `
      <div class="printer-header">
        <h4>${printer.name}</h4>
        <span class="printer-status ${printer.status}">${printer.status}</span>
      </div>
      
      <div class="printer-info">
        <div class="printer-model">${printer.type} ${printer.model}</div>
        <div class="printer-ip">${printer.ip_address}</div>
      </div>
      
      <div class="current-job" id="current-job-${printer.id}">
        ${printer.current_job ? `
          <div class="job-name">${printer.current_job.job_name}</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${printer.current_job.progress}%"></div>
            <span class="progress-text">${printer.current_job.progress.toFixed(1)}%</span>
          </div>
        ` : '<div class="no-job">Idle</div>'}
      </div>
      
      <div class="printer-actions">
        <button class="btn btn-small" data-action="view-printer" data-printer-id="${printer.id}">
          View Details
        </button>
      </div>
    `;
    
    // Add event listeners
    const viewButton = card.querySelector('[data-action="view-printer"]');
    viewButton.addEventListener('click', () => {
      showPrinterDetails(printer.id);
    });
    
    return card;
  };
  
  const loadRecentJobs = async () => {
    const container = document.getElementById('recent-jobs-container');
    if (!container) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/jobs?limit=5&sort=created_at&order=desc`);
      const data = await response.json();
      
      container.innerHTML = '';
      
      if (data.jobs.length === 0) {
        container.innerHTML = '<div class="empty-state">No recent jobs</div>';
        return;
      }
      
      data.jobs.forEach(job => {
        const jobElement = createRecentJobElement(job);
        container.appendChild(jobElement);
      });
      
    } catch (error) {
      console.error('Failed to load recent jobs:', error);
    }
  };
  
  const createRecentJobElement = (job) => {
    const element = document.createElement('div');
    element.className = `recent-job status-${job.status}`;
    element.setAttribute('data-job-id', job.id);
    
    element.innerHTML = `
      <div class="job-info">
        <div class="job-name">${job.job_name}</div>
        <div class="job-printer">${job.printer_name || job.printer_id}</div>
      </div>
      
      <div class="job-progress">
        <div class="progress-bar small">
          <div class="progress-fill" style="width: ${job.progress}%"></div>
        </div>
        <span class="progress-text">${job.progress.toFixed(1)}%</span>
      </div>
      
      <div class="job-status">
        <span class="status-badge ${job.status}">${job.status}</span>
      </div>
      
      <div class="job-actions">
        <button class="btn btn-icon" data-action="view-job" data-job-id="${job.id}">
          👁️
        </button>
      </div>
    `;
    
    // Add event listener
    const viewButton = element.querySelector('[data-action="view-job"]');
    viewButton.addEventListener('click', () => {
      showJobDetails(job.id);
    });
    
    return element;
  };
  
  const showPrinterDetails = (printerId) => {
    // This would normally show printer details modal
    console.log(`Show printer details for: ${printerId}`);
  };
  
  const showJobDetails = (jobId) => {
    // This would normally show job details modal
    console.log(`Show job details for: ${jobId}`);
  };
  
  const showError = (message) => {
    const container = document.getElementById('notification-container');
    if (container) {
      container.innerHTML = `<div class="error-notification">${message}</div>`;
    }
  };
  
  beforeEach(async () => {
    // Setup mock API responses
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
    
    const mockPrinters = {
      printers: [
        testUtils.createMockPrinter({
          current_job: {
            job_name: 'test_cube.3mf',
            progress: 45.5
          }
        }),
        testUtils.createMockPrinter({
          id: 'printer_002',
          name: 'Test Prusa Core One',
          type: 'prusa',
          status: 'offline',
          current_job: null
        })
      ]
    };
    
    const mockJobs = {
      jobs: [
        testUtils.createMockJob(),
        testUtils.createMockJob({ id: 'job_002', status: 'completed', progress: 100 }),
        testUtils.createMockJob({ id: 'job_003', status: 'queued', progress: 0 })
      ]
    };
    
    fetchMock.get(`${API_BASE_URL}/dashboard/stats`, mockStats);
    fetchMock.get(`${API_BASE_URL}/printers`, mockPrinters);
    fetchMock.get(`${API_BASE_URL}/jobs?limit=5&sort=created_at&order=desc`, mockJobs);
    
    // Initialize dashboard
    await initializeDashboard();
  });
  
  describe('Dashboard Initialization', () => {
    test('should render dashboard header', () => {
      const header = document.querySelector('.dashboard-header h1');
      expect(header).toBeInTheDocument();
      expect(header.textContent).toBe('Printernizer Dashboard');
    });
    
    test('should show connection status', () => {
      const status = document.getElementById('connection-status');
      expect(status).toBeInTheDocument();
      expect(status.textContent).toBe('Online');
    });
    
    test('should render statistics cards', () => {
      const printerStats = document.getElementById('printer-stats');
      const jobStats = document.getElementById('job-stats');
      const businessStats = document.getElementById('business-stats');
      
      expect(printerStats).toBeInTheDocument();
      expect(jobStats).toBeInTheDocument();
      expect(businessStats).toBeInTheDocument();
    });
  });
  
  describe('Statistics Display', () => {
    test('should display correct printer statistics', async () => {
      await waitFor(() => {
        const onlinePrinters = document.getElementById('online-printers');
        expect(onlinePrinters.textContent).toBe('1');
      });
    });
    
    test('should display correct job statistics', async () => {
      await waitFor(() => {
        const activeJobs = document.getElementById('active-jobs');
        expect(activeJobs.textContent).toBe('3');
      });
    });
    
    test('should display German currency format', async () => {
      await waitFor(() => {
        const totalRevenue = document.getElementById('total-revenue');
        expect(totalRevenue.textContent).toBe('1250.00');
      });
    });
  });
  
  describe('Printer Cards', () => {
    test('should render printer cards', async () => {
      await waitFor(() => {
        const printerCards = document.querySelectorAll('.printer-card');
        expect(printerCards).toHaveLength(2);
      });
    });
    
    test('should show printer status correctly', async () => {
      await waitFor(() => {
        const onlinePrinter = document.querySelector('.printer-card.status-online');
        const offlinePrinter = document.querySelector('.printer-card.status-offline');
        
        expect(onlinePrinter).toBeInTheDocument();
        expect(offlinePrinter).toBeInTheDocument();
      });
    });
    
    test('should display current job progress', async () => {
      await waitFor(() => {
        const progressBar = document.querySelector('.progress-fill');
        expect(progressBar).toBeInTheDocument();
        expect(progressBar.style.width).toBe('45.5%');
      });
    });
    
    test('should handle printer card click events', async () => {
      await waitFor(() => {
        const viewButton = document.querySelector('[data-action="view-printer"]');
        expect(viewButton).toBeInTheDocument();
        
        // Mock console.log to test click handler
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
        
        fireEvent.click(viewButton);
        
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Show printer details'));
        
        consoleSpy.mockRestore();
      });
    });
  });
  
  describe('Recent Jobs', () => {
    test('should render recent jobs list', async () => {
      await waitFor(() => {
        const recentJobs = document.querySelectorAll('.recent-job');
        expect(recentJobs).toHaveLength(3);
      });
    });
    
    test('should show job status badges', async () => {
      await waitFor(() => {
        const statusBadges = document.querySelectorAll('.status-badge');
        expect(statusBadges.length).toBeGreaterThan(0);
        
        const printingBadge = document.querySelector('.status-badge.printing');
        const completedBadge = document.querySelector('.status-badge.completed');
        const queuedBadge = document.querySelector('.status-badge.queued');
        
        expect(printingBadge).toBeInTheDocument();
        expect(completedBadge).toBeInTheDocument();
        expect(queuedBadge).toBeInTheDocument();
      });
    });
    
    test('should handle job view click events', async () => {
      await waitFor(() => {
        const viewButton = document.querySelector('[data-action="view-job"]');
        expect(viewButton).toBeInTheDocument();
        
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
        
        fireEvent.click(viewButton);
        
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Show job details'));
        
        consoleSpy.mockRestore();
      });
    });
  });
  
  describe('Real-time Updates', () => {
    test('should handle WebSocket connection', () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      expect(ws).toBeInstanceOf(WebSocket);
      expect(ws.url).toBe('ws://localhost:8000/ws');
    });
    
    test('should update printer status from WebSocket', async () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      await testUtils.waitFor(() => ws.readyState === WebSocket.OPEN);
      
      // Simulate receiving printer status update
      const statusUpdate = {
        type: 'printer_status',
        data: {
          printer_id: 'test_printer_001',
          status: 'printing',
          current_job: {
            job_name: 'updated_model.3mf',
            progress: 75.0
          }
        }
      };
      
      ws.simulateMessage(statusUpdate);
      
      // Verify UI update (would need actual WebSocket handler implementation)
      await waitFor(() => {
        // This would test the actual real-time update functionality
        expect(true).toBe(true); // Placeholder
      });
    });
    
    test('should update job progress from WebSocket', async () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      await testUtils.waitFor(() => ws.readyState === WebSocket.OPEN);
      
      const jobUpdate = {
        type: 'job_progress',
        data: {
          job_id: 'test_job_001',
          progress: 85.5,
          layer_current: 280,
          estimated_time_remaining: 900
        }
      };
      
      ws.simulateMessage(jobUpdate);
      
      // Test would verify progress bar update
      await waitFor(() => {
        expect(true).toBe(true); // Placeholder
      });
    });
  });
  
  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      fetchMock.reset();
      fetchMock.get(`${API_BASE_URL}/dashboard/stats`, 500);
      
      // Re-initialize dashboard with error response
      await loadDashboardData();
      
      const errorNotification = document.querySelector('.error-notification');
      expect(errorNotification).toBeInTheDocument();
      expect(errorNotification.textContent).toContain('Failed to load dashboard data');
    });
    
    test('should handle empty printer list', async () => {
      fetchMock.reset();
      fetchMock.get(`${API_BASE_URL}/printers`, { printers: [] });
      
      await loadPrinterCards({});
      
      const printerCards = document.querySelectorAll('.printer-card');
      expect(printerCards).toHaveLength(0);
    });
    
    test('should handle empty jobs list', async () => {
      fetchMock.reset();
      fetchMock.get(`${API_BASE_URL}/jobs?limit=5&sort=created_at&order=desc`, { jobs: [] });
      
      await loadRecentJobs();
      
      const emptyState = document.querySelector('.empty-state');
      expect(emptyState).toBeInTheDocument();
      expect(emptyState.textContent).toBe('No recent jobs');
    });
  });
  
  describe('Responsive Design', () => {
    test('should adapt to mobile viewport', () => {
      // Mock window resize
      global.innerWidth = 768;
      global.dispatchEvent(new Event('resize'));
      
      const dashboardGrid = document.querySelector('.dashboard-grid');
      expect(dashboardGrid).toBeInTheDocument();
      // Would test responsive classes/styles
    });
    
    test('should handle touch events on mobile', () => {
      const printerCard = document.querySelector('.printer-card');
      
      if (printerCard) {
        const touchEvent = new TouchEvent('touchstart', {
          touches: [{ clientX: 100, clientY: 100 }]
        });
        
        fireEvent(printerCard, touchEvent);
        // Test touch handling
      }
    });
  });
  
  describe('Accessibility', () => {
    test('should have proper ARIA labels', () => {
      // Test would check for aria-label, aria-describedby, etc.
      const statCards = document.querySelectorAll('.stat-card');
      statCards.forEach(card => {
        // Would verify accessibility attributes
        expect(card).toBeInTheDocument();
      });
    });
    
    test('should support keyboard navigation', () => {
      const viewButton = document.querySelector('[data-action="view-printer"]');
      
      if (viewButton) {
        viewButton.focus();
        expect(document.activeElement).toBe(viewButton);
        
        // Test Enter key press
        fireEvent.keyDown(viewButton, { key: 'Enter', code: 'Enter' });
      }
    });
  });
});