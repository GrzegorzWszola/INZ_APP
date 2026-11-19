import { fileURLToPath } from 'url';
import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { waitForAppReady, uploadEpub, waitForBookStatus } from './helpers';

const FIXTURE_EPUB = fileURLToPath(new URL('fixtures/test-book.epub', import.meta.url));
const BOOK_DISPLAY_NAME = 'Test Book'; // formatFileName('test-book.epub') → 'Test Book'

test.describe.serial('Book Reader full-stack flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await waitForAppReady(page);
  }); 

  test.afterAll(async () => {
    await page?.close();
  });

  test('1. App loads and shows Book Reader heading', async () => {
    await expect(page.getByRole('heading', { name: 'Book Reader' })).toBeVisible();
    await expect(page.getByText('Upload an EPUB file to parse and read.')).toBeVisible();
    // Upload button is disabled without a file
    await expect(page.getByRole('button', { name: 'Upload' })).toBeDisabled();
  });

  test('2. Upload an EPUB — book appears in list with "sent" status', async () => {
    await uploadEpub(page, FIXTURE_EPUB);
    // Book should appear in the list quickly
    const card = page.locator('.book-card', { hasText: BOOK_DISPLAY_NAME });
    await expect(card).toBeVisible({ timeout: 10_000 });
    // Status should be "sent" or already advancing
    const badge = card.locator('[class*="badge"]');
    await expect(badge).toBeVisible();
  });

  test('3. Book processes to "done" status (polling works)', async () => {
    test.setTimeout(6 * 60 * 1000);

    await waitForBookStatus(page, BOOK_DISPLAY_NAME, 'done', 6 * 60 * 1000);
    const card = page.locator('.book-card', { hasText: BOOK_DISPLAY_NAME });
    // "Read" button should be enabled when done
    await expect(card.getByRole('button', { name: 'Read' })).toBeEnabled();
  });

  test('4. Open book reader and navigate chapters', async () => {
    const card = page.locator('.book-card', { hasText: BOOK_DISPLAY_NAME });
    await card.getByRole('button', { name: 'Read' }).click();
    // BookReader overlay should appear with the book title
    await expect(page.getByText('Test Book')).toBeVisible({ timeout: 10_000 });
    // Chapter content should be visible (h2 in BookReader)
    await expect(page.getByText(/^1\..*/)).toBeVisible();
    // Close the reader — button uses title="Close reader" and renders ✕
    await page.getByTitle('Close reader').click();
    // Should be back on main page
    await expect(page.getByRole('heading', { name: 'Book Reader' })).toBeVisible();
  });

  test('5. Remove book from list', async () => {
    const card = page.locator('.book-card', { hasText: BOOK_DISPLAY_NAME });
    await expect(card).toBeVisible({ timeout: 10_000 });
    await card.getByRole('button', { name: 'Remove' }).click();
    // Book card should disappear
    await expect(card).not.toBeVisible({ timeout: 10_000 });
  });

});
