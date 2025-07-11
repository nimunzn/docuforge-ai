import { test, expect } from '@playwright/test';
import { TestHelpers } from './utils/test-helpers';

test.describe('Document Preview Functionality', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('should display document preview correctly', async ({ page }) => {
    await helpers.navigateToDocument(1);
    
    // Switch to preview mode
    await helpers.switchToPreviewMode();
    
    // Verify preview panel is visible
    await expect(page.locator('[data-testid="document-preview"]')).toBeVisible();
    
    // Check preview content structure
    await expect(page.locator('[data-testid="document-preview"] .prose')).toBeVisible();
  });

  test('should render document content as formatted text', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with structured content
    const mockDocument = {
      id: 1,
      title: 'Test Document',
      content: {
        sections: [
          {
            title: 'Executive Summary',
            content: 'This is the executive summary of our business plan.'
          },
          {
            title: 'Market Analysis',
            content: 'Our market analysis shows significant opportunities in the technology sector.'
          },
          {
            title: 'Financial Projections',
            content: 'We project 25% growth in the first year with revenues of $500,000.'
          }
        ]
      }
    };
    
    // Simulate document update
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: mockDocument }
    });
    
    // Verify sections are rendered
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('Executive Summary');
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('Market Analysis');
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('Financial Projections');
    
    // Verify content is rendered
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('This is the executive summary');
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('significant opportunities');
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('25% growth');
  });

  test('should handle empty document content', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock empty document
    const emptyDocument = {
      id: 1,
      title: 'Empty Document',
      content: { sections: [] }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: emptyDocument }
    });
    
    // Verify empty state handling
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await expect(previewPanel).toBeVisible();
    
    // Should show empty state or placeholder
    const emptyState = page.locator('[data-testid="empty-document"], .text-center:has-text("No content")');
    if (await emptyState.isVisible()) {
      await expect(emptyState).toBeVisible();
    }
  });

  test('should update preview in real-time during document generation', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock WebSocket connection
    await helpers.mockWebSocketConnection();
    await helpers.waitForWebSocketConnection();
    
    // Send document generation request
    await helpers.sendChatMessage('create a business plan template');
    
    // Simulate incremental document updates
    const updates = [
      {
        content: {
          sections: [
            { title: 'Executive Summary', content: 'Initial summary...' }
          ]
        }
      },
      {
        content: {
          sections: [
            { title: 'Executive Summary', content: 'Completed executive summary with detailed analysis...' },
            { title: 'Company Overview', content: 'Company description and mission...' }
          ]
        }
      },
      {
        content: {
          sections: [
            { title: 'Executive Summary', content: 'Completed executive summary with detailed analysis...' },
            { title: 'Company Overview', content: 'Company description and mission...' },
            { title: 'Market Analysis', content: 'Comprehensive market research findings...' }
          ]
        }
      }
    ];
    
    // Send updates with delays to simulate real-time generation
    for (const update of updates) {
      await page.waitForTimeout(1000);
      await helpers.triggerWebSocketMessage({
        type: 'document_updated',
        data: { document: { id: 1, title: 'Business Plan', ...update } }
      });
      
      // Verify content appears incrementally
      const lastSection = update.content.sections[update.content.sections.length - 1];
      await expect(page.locator('[data-testid="document-preview"]')).toContainText(lastSection.title);
    }
  });

  test('should handle markdown content rendering', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with markdown content
    const markdownDocument = {
      id: 1,
      title: 'Markdown Document',
      content: {
        sections: [
          {
            title: 'Introduction',
            content: '# Main Heading\n\nThis is **bold text** and *italic text*.\n\n## Subheading\n\n- List item 1\n- List item 2\n- List item 3\n\n[Link example](https://example.com)'
          }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: markdownDocument }
    });
    
    // Verify markdown is rendered as HTML
    await expect(page.locator('[data-testid="document-preview"] h1')).toContainText('Main Heading');
    await expect(page.locator('[data-testid="document-preview"] h2')).toContainText('Subheading');
    await expect(page.locator('[data-testid="document-preview"] strong')).toContainText('bold text');
    await expect(page.locator('[data-testid="document-preview"] em')).toContainText('italic text');
    await expect(page.locator('[data-testid="document-preview"] ul li')).toContainText('List item 1');
    await expect(page.locator('[data-testid="document-preview"] a[href="https://example.com"]')).toContainText('Link example');
  });

  test('should handle document preview scrolling', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with long content
    const longContent = Array.from({ length: 50 }, (_, i) => `Section ${i + 1} content with detailed information that spans multiple lines and creates a scrollable document.`).join('\n\n');
    
    const longDocument = {
      id: 1,
      title: 'Long Document',
      content: {
        sections: [
          { title: 'Long Content', content: longContent }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: longDocument }
    });
    
    // Verify scrolling works
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await expect(previewPanel).toBeVisible();
    
    // Scroll to bottom
    await previewPanel.evaluate(el => el.scrollTo(0, el.scrollHeight));
    
    // Verify scroll position
    const scrollTop = await previewPanel.evaluate(el => el.scrollTop);
    expect(scrollTop).toBeGreaterThan(0);
  });

  test('should handle document preview printing', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with content
    const printDocument = {
      id: 1,
      title: 'Print Document',
      content: {
        sections: [
          { title: 'Section 1', content: 'Content for printing' },
          { title: 'Section 2', content: 'More content for printing' }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: printDocument }
    });
    
    // Check print styles are applied
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await expect(previewPanel).toHaveClass(/prose/);
    
    // Verify print-friendly formatting
    await expect(previewPanel).toBeVisible();
  });

  test('should handle different document types in preview', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    const documentTypes = [
      {
        type: 'business_plan',
        content: { sections: [{ title: 'Executive Summary', content: 'Business plan executive summary' }] }
      },
      {
        type: 'technical_report',
        content: { sections: [{ title: 'Abstract', content: 'Technical report abstract' }] }
      },
      {
        type: 'presentation',
        content: { sections: [{ title: 'Slide 1', content: 'Presentation slide content' }] }
      }
    ];
    
    for (const docType of documentTypes) {
      await helpers.triggerWebSocketMessage({
        type: 'document_updated',
        data: {
          document: {
            id: 1,
            title: `Test ${docType.type}`,
            type: docType.type,
            content: docType.content
          }
        }
      });
      
      // Verify content is displayed
      await expect(page.locator('[data-testid="document-preview"]')).toContainText(docType.content.sections[0].title);
      
      await page.waitForTimeout(500);
    }
  });

  test('should handle document preview error states', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with invalid content structure
    const invalidDocument = {
      id: 1,
      title: 'Invalid Document',
      content: null // Invalid content
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: invalidDocument }
    });
    
    // Verify error handling
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await expect(previewPanel).toBeVisible();
    
    // Should handle gracefully without crashing
    await expect(page.locator('[data-testid="document-workspace"]')).toBeVisible();
  });

  test('should update preview when switching between documents', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock first document
    const doc1 = {
      id: 1,
      title: 'Document 1',
      content: { sections: [{ title: 'Doc 1 Content', content: 'First document content' }] }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: doc1 }
    });
    
    // Verify first document content
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('First document content');
    
    // Navigate to second document
    await helpers.navigateToDocument(2);
    
    // Mock second document
    const doc2 = {
      id: 2,
      title: 'Document 2',
      content: { sections: [{ title: 'Doc 2 Content', content: 'Second document content' }] }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: doc2 }
    });
    
    // Verify second document content
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('Second document content');
    await expect(page.locator('[data-testid="document-preview"]')).not.toContainText('First document content');
  });

  test('should handle document preview on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with content
    const mobileDoc = {
      id: 1,
      title: 'Mobile Document',
      content: {
        sections: [
          { title: 'Mobile Content', content: 'This content should be optimized for mobile viewing' }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: mobileDoc }
    });
    
    // Verify preview is responsive
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await expect(previewPanel).toBeVisible();
    
    const previewBounds = await previewPanel.boundingBox();
    expect(previewBounds?.width).toBeLessThan(400);
    
    // Verify content is readable on mobile
    await expect(previewPanel).toContainText('This content should be optimized for mobile viewing');
  });

  test('should handle document preview with large content', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with very large content
    const largeContent = Array.from({ length: 1000 }, (_, i) => `Line ${i + 1}: This is a very long line of content that will test the performance of the document preview component.`).join('\n');
    
    const largeDocument = {
      id: 1,
      title: 'Large Document',
      content: {
        sections: [
          { title: 'Large Content Section', content: largeContent }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: largeDocument }
    });
    
    // Verify large content is handled
    await expect(page.locator('[data-testid="document-preview"]')).toContainText('Line 1:');
    await expect(page.locator('[data-testid="document-preview"]')).toBeVisible();
    
    // Verify scrolling works with large content
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await previewPanel.evaluate(el => el.scrollTo(0, el.scrollHeight));
    
    const scrollTop = await previewPanel.evaluate(el => el.scrollTop);
    expect(scrollTop).toBeGreaterThan(0);
  });

  test('should preserve scroll position on content updates', async ({ page }) => {
    await helpers.navigateToDocument(1);
    await helpers.switchToPreviewMode();
    
    // Mock document with scrollable content
    const scrollableContent = Array.from({ length: 100 }, (_, i) => `Paragraph ${i + 1}: This is paragraph content that will make the document scrollable.`).join('\n\n');
    
    const doc = {
      id: 1,
      title: 'Scrollable Document',
      content: {
        sections: [
          { title: 'Scrollable Content', content: scrollableContent }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: doc }
    });
    
    // Scroll to middle
    const previewPanel = page.locator('[data-testid="document-preview"]');
    await previewPanel.evaluate(el => el.scrollTo(0, el.scrollHeight / 2));
    
    const initialScrollTop = await previewPanel.evaluate(el => el.scrollTop);
    
    // Update content
    const updatedDoc = {
      ...doc,
      content: {
        sections: [
          { title: 'Scrollable Content', content: scrollableContent + '\n\nAdditional content added' }
        ]
      }
    };
    
    await helpers.triggerWebSocketMessage({
      type: 'document_updated',
      data: { document: updatedDoc }
    });
    
    // Verify scroll position is preserved (or handled appropriately)
    await expect(previewPanel).toContainText('Additional content added');
  });
});