import { test, expect } from '@playwright/test';
import { TestHelpers } from './utils/test-helpers';

test.describe('Document Creation and Editing', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('should create a new document from document list', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if create button is available
    const createButton = page.locator('a:has-text("Create Document")');
    
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Verify navigation to create page
      await expect(page).toHaveURL(/\/create/);
      
      // Fill document creation form
      await page.locator('input[name="title"]').fill('Test Document');
      await page.locator('select[name="type"]').selectOption('business_plan');
      
      // Submit form
      await page.locator('button[type="submit"]').click();
      
      // Verify navigation to document workspace
      await expect(page).toHaveURL(/\/document\/\d+/);
      await helpers.waitForAppToLoad();
    }
  });

  test('should display document workspace correctly', async ({ page }) => {
    // Navigate to a document (assuming document ID 1 exists)
    await helpers.navigateToDocument(1);
    
    // Verify workspace layout
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
    
    // Check header elements
    await expect(page.locator('[data-testid="document-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="document-type"]')).toBeVisible();
    await expect(page.locator('[data-testid="document-status"]')).toBeVisible();
    
    // Check mode toggle buttons
    await expect(page.locator('button:has-text("Preview")')).toBeVisible();
    await expect(page.locator('button:has-text("Edit")')).toBeVisible();
    
    // Check export button
    await expect(page.locator('button:has-text("Export")')).toBeVisible();
    
    // Check two-panel layout
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
    await expect(page.locator('[data-testid="document-preview"]')).toBeVisible();
    
    // Check resize handle
    await expect(page.locator('[data-testid="resize-handle"]')).toBeVisible();
  });

  test('should switch between preview and edit modes', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Start in preview mode
    await helpers.switchToPreviewMode();
    
    // Verify preview mode is active
    await expect(page.locator('button:has-text("Preview")')).toHaveClass(/bg-white text-blue-600/);
    await expect(page.locator('[data-testid="document-preview"]')).toBeVisible();
    
    // Switch to edit mode
    await helpers.switchToEditMode();
    
    // Verify edit mode is active
    await expect(page.locator('button:has-text("Edit")')).toHaveClass(/bg-white text-blue-600/);
    await expect(page.locator('[data-testid="document-editor"]')).toBeVisible();
  });

  test('should resize chat panel correctly', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Get initial panel width
    const chatPanel = page.locator('[data-testid="chat-panel"]');
    const initialBounds = await chatPanel.boundingBox();
    
    // Resize panel
    await helpers.resizeChatPanel(60);
    
    // Wait for resize to complete
    await page.waitForTimeout(500);
    
    // Verify panel width changed
    const newBounds = await chatPanel.boundingBox();
    expect(newBounds?.width).not.toBe(initialBounds?.width);
  });

  test('should display document statistics', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check document statistics
    await expect(page.locator('[data-testid="word-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="character-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="reading-time"]')).toBeVisible();
    await expect(page.locator('[data-testid="created-date"]')).toBeVisible();
    await expect(page.locator('[data-testid="updated-date"]')).toBeVisible();
    
    // Verify statistics format
    const wordCount = await page.locator('[data-testid="word-count"]').textContent();
    expect(wordCount).toMatch(/\d+ words/);
    
    const readingTime = await page.locator('[data-testid="reading-time"]').textContent();
    expect(readingTime).toMatch(/\d+ min read/);
  });

  test('should export document in different formats', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Test PDF export
    const pdfDownload = await helpers.exportDocument('pdf');
    expect(pdfDownload.suggestedFilename()).toMatch(/\.pdf$/);
    
    // Test Word export
    const docxDownload = await helpers.exportDocument('docx');
    expect(docxDownload.suggestedFilename()).toMatch(/\.docx$/);
    
    // Test PowerPoint export
    const pptxDownload = await helpers.exportDocument('pptx');
    expect(pptxDownload.suggestedFilename()).toMatch(/\.pptx$/);
  });

  test('should handle export errors gracefully', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock export failure
    await page.route('**/documents/*/export', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Export failed' })
      });
    });
    
    // Try to export
    await page.locator('button:has-text("Export")').click();
    await page.locator('button:has-text("Export as PDF")').click();
    
    // Verify error message appears
    await helpers.verifyErrorMessage('Failed to export document');
  });

  test('should display provider selector', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check provider selector
    await expect(page.locator('[data-testid="provider-selector"]')).toBeVisible();
    
    // Check model label
    await expect(page.locator('span:has-text("Model:")')).toBeVisible();
  });

  test('should handle document loading errors', async ({ page }) => {
    // Try to navigate to non-existent document
    await helpers.navigateToDocument(999999);
    
    // Verify error state
    await expect(page.locator('.text-gray-500:has-text("Document not found")')).toBeVisible();
  });

  test('should display document creation date', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check creation date format
    const createdDate = page.locator('[data-testid="created-date"]');
    await expect(createdDate).toBeVisible();
    
    const dateText = await createdDate.textContent();
    expect(dateText).toMatch(/Created \d+\/\d+\/\d+/);
  });

  test('should display save status', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check save status
    const saveStatus = page.locator('[data-testid="save-status"]');
    await expect(saveStatus).toBeVisible();
    
    const saveText = await saveStatus.textContent();
    expect(saveText).toMatch(/Saved \d+:\d+:\d+/);
  });

  test('should handle document updates via WebSocket', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    
    // Wait for connection
    await helpers.waitForWebSocketConnection();
    
    // Simulate document update
    const updateMessage = {
      type: 'document_updated',
      document: {
        id: 1,
        title: 'Updated Test Document',
        content: { sections: [{ title: 'Test Section', content: 'Updated content' }] }
      }
    };
    
    await helpers.triggerWebSocketMessage(updateMessage);
    
    // Verify document title updated
    await expect(page.locator('[data-testid="document-title"]')).toContainText('Updated Test Document');
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await helpers.navigateToDocument(1);
    
    // Check responsive layout
    const workspace = page.locator('[data-testid="document-workspace"]');
    await expect(workspace).toBeVisible();
    
    // Check panels are properly sized
    const chatPanel = page.locator('[data-testid="chat-panel"]');
    const previewPanel = page.locator('[data-testid="document-preview"]');
    
    const chatBounds = await chatPanel.boundingBox();
    const previewBounds = await previewPanel.boundingBox();
    
    expect(chatBounds?.width).toBeLessThan(400);
    expect(previewBounds?.width).toBeLessThan(400);
  });

  test('should handle panel resizing edge cases', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Test minimum width constraint
    await helpers.resizeChatPanel(10); // Very small percentage
    
    const chatPanel = page.locator('[data-testid="chat-panel"]');
    const bounds = await chatPanel.boundingBox();
    
    // Should respect minimum width (25%)
    const viewport = page.viewportSize();
    if (viewport) {
      const minWidth = (viewport.width * 25) / 100;
      expect(bounds?.width).toBeGreaterThanOrEqual(minWidth - 10); // Small tolerance
    }
    
    // Test maximum width constraint
    await helpers.resizeChatPanel(90); // Very large percentage
    
    const newBounds = await chatPanel.boundingBox();
    if (viewport) {
      const maxWidth = (viewport.width * 65) / 100;
      expect(newBounds?.width).toBeLessThanOrEqual(maxWidth + 10); // Small tolerance
    }
  });

  test('should display document type badge', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check document type is displayed
    const typeElement = page.locator('[data-testid="document-type"]');
    await expect(typeElement).toBeVisible();
    
    const typeText = await typeElement.textContent();
    expect(typeText).toBeTruthy();
  });

  test('should handle loading states correctly', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Check loading state appears briefly
    try {
      await expect(page.locator('.text-gray-500:has-text("Loading document")')).toBeVisible({ timeout: 2000 });
    } catch {
      // Loading might have completed too quickly
    }
    
    // Wait for loading to complete
    await helpers.waitForLoadingToComplete();
    
    // Verify document workspace is loaded
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
  });
});