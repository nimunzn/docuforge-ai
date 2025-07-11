import { test, expect } from '@playwright/test';
import { TestHelpers } from './utils/test-helpers';

test.describe('Document List', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('should display document list page', async ({ page }) => {
    await helpers.navigateToDocumentList();
    
    // Check page title and header
    await expect(page.locator('h2:has-text("Documents")')).toBeVisible();
    await expect(page.locator('p:has-text("Manage your AI-generated documents")')).toBeVisible();
    
    // Check search bar is present
    await expect(page.locator('input[placeholder="Search documents..."]')).toBeVisible();
  });

  test('should show empty state when no documents exist', async ({ page }) => {
    await helpers.navigateToDocumentList();
    
    // Wait for loading to complete
    await helpers.waitForLoadingToComplete();
    
    // Check empty state
    const emptyState = page.locator('[data-testid="empty-state"], .text-center:has-text("No documents yet")');
    if (await emptyState.isVisible()) {
      await expect(page.locator('h3:has-text("No documents yet")')).toBeVisible();
      await expect(page.locator('p:has-text("Create your first document to get started")')).toBeVisible();
      await expect(page.locator('a:has-text("Create Document")')).toBeVisible();
    }
  });

  test('should display document cards when documents exist', async ({ page }) => {
    await helpers.navigateToDocumentList();
    
    // Wait for loading to complete
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Verify document card structure
      const firstCard = documentCards.first();
      await expect(firstCard).toBeVisible();
      
      // Check card elements
      await expect(firstCard.locator('[data-testid="document-title"]')).toBeVisible();
      await expect(firstCard.locator('[data-testid="document-type"]')).toBeVisible();
      await expect(firstCard.locator('[data-testid="document-status"]')).toBeVisible();
      await expect(firstCard.locator('[data-testid="document-updated"]')).toBeVisible();
      
      // Check action buttons
      await expect(firstCard.locator('a:has-text("Edit")')).toBeVisible();
      await expect(firstCard.locator('button[data-testid="export-button"]')).toBeVisible();
      await expect(firstCard.locator('button[data-testid="delete-button"]')).toBeVisible();
    }
  });

  test('should search documents', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Get first document title
      const firstCard = documentCards.first();
      const titleElement = firstCard.locator('[data-testid="document-title"]');
      const title = await titleElement.textContent();
      
      if (title) {
        // Search for the document
        await helpers.searchDocuments(title);
        
        // Verify search results
        const searchResults = await helpers.getDocumentCards();
        const resultCount = await searchResults.count();
        
        expect(resultCount).toBeGreaterThan(0);
        await expect(searchResults.first()).toContainText(title);
      }
    }
  });

  test('should filter documents by search term', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Search for non-existent term
    await helpers.searchDocuments('nonexistentdocument12345');
    
    // Should show no results
    const noResults = page.locator('[data-testid="no-results"], .text-center:has-text("No documents found")');
    await expect(noResults).toBeVisible();
  });

  test('should navigate to document when clicking Edit button', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Click Edit button on first document
      const firstCard = documentCards.first();
      const editButton = firstCard.locator('a:has-text("Edit")');
      await editButton.click();
      
      // Verify navigation to document workspace
      await expect(page).toHaveURL(/\/document\/\d+/);
      
      // Verify document workspace elements
      await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
      await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
      await expect(page.locator('[data-testid="document-preview"]')).toBeVisible();
    }
  });

  test('should show export dropdown on hover', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Hover over export button
      const firstCard = documentCards.first();
      const exportButton = firstCard.locator('button[data-testid="export-button"]');
      await exportButton.hover();
      
      // Check export options appear
      await expect(page.locator('button:has-text("Export PDF")')).toBeVisible();
      await expect(page.locator('button:has-text("Export Word")')).toBeVisible();
      await expect(page.locator('button:has-text("Export PPT")')).toBeVisible();
    }
  });

  test('should select documents with checkboxes', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Select first document
      const firstCard = documentCards.first();
      const checkbox = firstCard.locator('input[type="checkbox"]');
      await checkbox.check();
      
      // Verify selection bar appears
      await expect(page.locator('[data-testid="selection-bar"]')).toBeVisible();
      await expect(page.locator('span:has-text("1 document(s) selected")')).toBeVisible();
      
      // Verify bulk action buttons
      await expect(page.locator('button:has-text("Export Selected")')).toBeVisible();
      await expect(page.locator('button:has-text("Delete Selected")')).toBeVisible();
    }
  });

  test('should handle document deletion', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Get initial document count
      const initialCount = await documentCards.count();
      
      // Click delete button on first document
      const firstCard = documentCards.first();
      const deleteButton = firstCard.locator('button[data-testid="delete-button"]');
      
      // Set up dialog handler
      page.on('dialog', async dialog => {
        expect(dialog.type()).toBe('confirm');
        expect(dialog.message()).toContain('Are you sure you want to delete this document?');
        await dialog.accept();
      });
      
      await deleteButton.click();
      
      // Wait for deletion to complete
      await page.waitForTimeout(1000);
      
      // Verify document count decreased or empty state appears
      const updatedCards = await helpers.getDocumentCards();
      const updatedCount = await updatedCards.count();
      
      expect(updatedCount).toBeLessThan(initialCount);
    }
  });

  test('should display document status correctly', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Check status badge on first document
      const firstCard = documentCards.first();
      const statusBadge = firstCard.locator('[data-testid="document-status"]');
      
      await expect(statusBadge).toBeVisible();
      
      // Verify status is one of the expected values
      const statusText = await statusBadge.textContent();
      expect(['draft', 'published', 'archived']).toContain(statusText?.toLowerCase());
    }
  });

  test('should display document update date', async ({ page }) => {
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Check update date on first document
      const firstCard = documentCards.first();
      const updateElement = firstCard.locator('[data-testid="document-updated"]');
      
      await expect(updateElement).toBeVisible();
      
      // Verify update text format
      const updateText = await updateElement.textContent();
      expect(updateText).toMatch(/Updated \d+\/\d+\/\d+/);
    }
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await helpers.navigateToDocumentList();
    await helpers.waitForLoadingToComplete();
    
    // Check responsive layout
    const gridContainer = page.locator('[data-testid="documents-grid"]');
    await expect(gridContainer).toBeVisible();
    
    // Check if documents exist
    const documentCards = await helpers.getDocumentCards();
    const cardCount = await documentCards.count();
    
    if (cardCount > 0) {
      // Verify cards are properly sized for mobile
      const firstCard = documentCards.first();
      const cardBounds = await firstCard.boundingBox();
      
      expect(cardBounds?.width).toBeLessThan(400); // Should fit mobile screen
    }
  });

  test('should handle loading states', async ({ page }) => {
    await helpers.navigateToDocumentList();
    
    // Check loading state appears briefly
    try {
      await expect(page.locator('[data-testid="loading"], .text-gray-500:has-text("Loading")')).toBeVisible({ timeout: 2000 });
    } catch {
      // Loading might have completed too quickly
    }
    
    // Wait for loading to complete
    await helpers.waitForLoadingToComplete();
    
    // Verify content is loaded
    await expect(page.locator('h2:has-text("Documents")')).toBeVisible();
  });
});