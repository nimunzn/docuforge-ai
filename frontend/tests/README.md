# DocuForge AI Frontend Tests

This directory contains comprehensive end-to-end tests for the DocuForge AI frontend application using Playwright.

## Test Structure

### Test Files

- **`document-list.spec.ts`** - Tests for the document list page functionality
- **`document-creation.spec.ts`** - Tests for document creation and workspace functionality
- **`chat-interactions.spec.ts`** - Tests for chat interface and document generation
- **`websocket.spec.ts`** - Tests for WebSocket connections and real-time updates
- **`document-preview.spec.ts`** - Tests for document preview functionality

### Utilities

- **`utils/test-helpers.ts`** - Shared helper functions for common test actions

## Running Tests

### Prerequisites

1. Ensure the frontend development server is running:
   ```bash
   npm run dev
   ```

2. Ensure the backend server is running on `http://localhost:8000`

### Test Commands

```bash
# Run all tests
npm test

# Run tests in headed mode (with browser UI)
npm run test:headed

# Run tests with interactive UI
npm run test:ui

# Debug tests
npm run test:debug

# Show test report
npm run test:report

# Run specific test file
npx playwright test document-list.spec.ts

# Run tests on specific browser
npx playwright test --project=chromium

# Run tests in parallel
npx playwright test --workers=4
```

## Test Coverage

### Document List Tests
- ✅ Display document list page correctly
- ✅ Show empty state when no documents exist
- ✅ Display document cards with proper structure
- ✅ Search and filter documents
- ✅ Navigate to document workspace
- ✅ Handle document selection and bulk actions
- ✅ Export and delete documents
- ✅ Responsive design on mobile devices

### Document Creation Tests
- ✅ Create new documents from document list
- ✅ Display document workspace layout
- ✅ Switch between preview and edit modes
- ✅ Resize chat panel
- ✅ Display document statistics
- ✅ Export documents in different formats
- ✅ Handle loading and error states
- ✅ WebSocket integration for real-time updates

### Chat Interactions Tests
- ✅ Display chat interface correctly
- ✅ Handle suggestion buttons
- ✅ Send and receive chat messages
- ✅ Create business plan templates
- ✅ Agent process tracking and visualization
- ✅ Streaming response handling
- ✅ Keyboard shortcuts (Enter, Shift+Enter)
- ✅ Input validation and error handling
- ✅ Document generation workflows

### WebSocket Tests
- ✅ Establish WebSocket connections
- ✅ Receive document updates in real-time
- ✅ Handle chat messages via WebSocket
- ✅ Connection error handling and recovery
- ✅ Malformed message handling
- ✅ Real-time document preview updates
- ✅ Connection cleanup on navigation
- ✅ Multiple connection handling

### Document Preview Tests
- ✅ Display document preview correctly
- ✅ Render formatted content (markdown, HTML)
- ✅ Handle empty document states
- ✅ Real-time preview updates during generation
- ✅ Scrolling and large content handling
- ✅ Different document types support
- ✅ Mobile responsiveness
- ✅ Error state handling

## Test Data

Tests use mock data and WebSocket simulation to ensure consistent testing without requiring specific backend data. The tests are designed to:

1. Work with any document IDs (falling back gracefully if documents don't exist)
2. Mock WebSocket connections for reliable testing
3. Simulate real user interactions
4. Test error conditions and edge cases

## Key Features Tested

### Real User Simulation
- Tests mimic actual user workflows
- Realistic timing and interactions
- Proper error handling and recovery

### Core Functionality
- Document creation and management
- Chat interface with AI agents
- Real-time document updates
- WebSocket communication
- Export functionality

### Edge Cases
- Empty states and error conditions
- Network failures and timeouts
- Large document content
- Mobile responsiveness
- Connection recovery

### Performance
- Large document handling
- Scrolling performance
- Real-time update efficiency
- Memory usage optimization

## Browser Support

Tests run on:
- **Chromium** - Desktop Chrome
- **Firefox** - Desktop Firefox
- **WebKit** - Desktop Safari
- **Mobile Chrome** - Pixel 5 simulation
- **Mobile Safari** - iPhone 12 simulation

## Continuous Integration

Tests are configured to run in CI environments with:
- Automatic retry on failure
- Screenshot capture on failure
- Video recording for debugging
- HTML report generation
- Parallel execution for speed

## Debugging

### Visual Debugging
```bash
# Run with browser UI visible
npm run test:headed

# Interactive debugging
npm run test:ui

# Debug specific test
npx playwright test --debug document-list.spec.ts
```

### Screenshots and Videos
- Screenshots are captured on test failure
- Videos are recorded for failed tests
- Reports include visual debugging information

### Logs
- Console logs are captured during tests
- Network requests are logged
- WebSocket messages are tracked

## Best Practices

### Test Organization
- Each test file focuses on a specific area
- Helper functions reduce code duplication
- Tests are independent and can run in any order

### Reliability
- Tests wait for elements to be ready
- Network requests are properly mocked
- Race conditions are avoided

### Maintainability
- Clear test descriptions and comments
- Consistent naming conventions
- Reusable utility functions

## Adding New Tests

1. Create test files in the appropriate category
2. Use the `TestHelpers` class for common actions
3. Follow the existing naming and structure patterns
4. Include both positive and negative test cases
5. Test responsive design and accessibility
6. Mock external dependencies appropriately

## Troubleshooting

### Common Issues

1. **Tests timeout**: Increase timeout values in `playwright.config.ts`
2. **WebSocket connection fails**: Check backend server is running
3. **Elements not found**: Verify element selectors match the actual DOM
4. **Flaky tests**: Add proper wait conditions and remove hardcoded delays

### Environment Setup

Ensure your development environment has:
- Node.js and npm installed
- Frontend server running on port 5173
- Backend server running on port 8000
- All dependencies installed (`npm install`)

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use the shared helper functions
3. Include comprehensive test coverage
4. Test both success and failure scenarios
5. Update this README with new test descriptions