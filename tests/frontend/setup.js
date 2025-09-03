/**
 * Jest setup file for frontend tests
 * Configures testing environment, polyfills, and global mocks
 */
import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';
import fetchMock from 'fetch-mock';

// Polyfills for Node.js environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock WebSocket for testing
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen({ type: 'open' });
    }, 10);
  }
  
  send(data) {
    if (this.readyState === WebSocket.OPEN) {
      // Echo back for testing
      setTimeout(() => {
        if (this.onmessage) {
          this.onmessage({ data });
        }
      }, 10);
    }
  }
  
  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose({ type: 'close' });
  }
  
  // Simulate receiving a message
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }
}

MockWebSocket.CONNECTING = 0;
MockWebSocket.OPEN = 1;
MockWebSocket.CLOSING = 2;
MockWebSocket.CLOSED = 3;

global.WebSocket = MockWebSocket;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock sessionStorage
global.sessionStorage = localStorageMock;

// Mock fetch if not using fetch-mock
global.fetch = fetchMock.sandbox();

// Mock console methods for cleaner test output
const originalError = console.error;
console.error = (...args) => {
  if (typeof args[0] === 'string' && args[0].includes('Warning:')) {
    return;
  }
  originalError.call(console, ...args);
};

// Setup DOM environment
document.body.innerHTML = '';

// Mock intersection observer
global.IntersectionObserver = class MockIntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock resize observer
global.ResizeObserver = class MockResizeObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock canvas context for any potential 3D preview testing
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn(() => ({ data: new Array(4) })),
  putImageData: jest.fn(),
  createImageData: jest.fn(() => []),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  fillText: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  stroke: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  measureText: jest.fn(() => ({ width: 0 })),
  transform: jest.fn(),
  rect: jest.fn(),
  clip: jest.fn(),
}));

// Global test utilities
global.testUtils = {
  // Create mock API response
  createApiResponse: (data, status = 200) => ({
    status,
    ok: status >= 200 && status < 300,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers({ 'content-type': 'application/json' })
  }),
  
  // Create mock printer data
  createMockPrinter: (overrides = {}) => ({
    id: 'test_printer_001',
    name: 'Test Bambu A1',
    type: 'bambu_lab',
    model: 'A1',
    status: 'online',
    ip_address: '192.168.1.100',
    has_camera: true,
    has_ams: true,
    current_job: null,
    ...overrides
  }),
  
  // Create mock job data
  createMockJob: (overrides = {}) => ({
    id: 'test_job_001',
    printer_id: 'test_printer_001',
    job_name: 'test_model.3mf',
    status: 'printing',
    progress: 45.5,
    layer_current: 150,
    layer_total: 330,
    estimated_time_remaining: 2700,
    material_type: 'PLA',
    material_color: 'White',
    is_business: false,
    ...overrides
  }),
  
  // Create mock file data
  createMockFile: (overrides = {}) => ({
    id: 'test_file_001',
    filename: 'test_model.3mf',
    file_size: 2048000,
    printer_id: 'test_printer_001',
    download_status: 'available',
    location: 'printer',
    file_type: '.3mf',
    ...overrides
  }),
  
  // Wait for async operations
  waitFor: async (fn, timeout = 1000) => {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      try {
        const result = await fn();
        if (result) return result;
      } catch (error) {
        // Continue waiting
      }
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    throw new Error('Timeout waiting for condition');
  },
  
  // Trigger DOM event
  triggerEvent: (element, eventType, eventInit = {}) => {
    const event = new Event(eventType, { bubbles: true, cancelable: true, ...eventInit });
    element.dispatchEvent(event);
    return event;
  }
};

// Setup fetch mock defaults
fetchMock.config.overwriteRoutes = true;

beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
  fetchMock.reset();
  
  // Reset DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
  
  // Add basic DOM structure that Printernizer expects
  document.body.innerHTML = `
    <div id="app">
      <nav id="main-nav"></nav>
      <main id="main-content">
        <div id="dashboard-view" class="view"></div>
        <div id="printers-view" class="view" style="display: none;"></div>
        <div id="jobs-view" class="view" style="display: none;"></div>
        <div id="files-view" class="view" style="display: none;"></div>
      </main>
      <div id="modal-container"></div>
      <div id="notification-container"></div>
    </div>
  `;
});

afterEach(() => {
  // Clean up after each test
  fetchMock.reset();
});