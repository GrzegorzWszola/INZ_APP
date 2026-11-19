import { type Page } from '@playwright/test';

/** Wait for the app to be ready (session initialized, books loaded) */
export async function waitForAppReady(page: Page) {
  await page.goto('/');
  // Wait for the main header to be visible
  await page.waitForSelector('h1', { timeout: 15000 });
}

/** Upload an EPUB fixture file via the UI */
export async function uploadEpub(page: Page, filePath: string) {
  const fileInput = page.locator('input[type="file"][accept=".epub"]');
  await fileInput.setInputFiles(filePath);
  await page.getByRole('button', { name: 'Upload' }).click();
}

/** Wait until a book card reaches a given status badge, or fails immediately if status becomes error */
export async function waitForBookStatus(
  page: Page,
  filename: string,
  targetStatus: string,
  timeout = 360_000
) {
  const card = page.locator('.book-card', { hasText: filename });

  // Wait for either the target status or an error status
  const targetBadge = card.locator(`.badge-${targetStatus}`);
  const errorBadge = card.locator('.badge-error');

  const result = await Promise.race([
    targetBadge.waitFor({ timeout }).then(() => 'target' as const),
    errorBadge.waitFor({ timeout }).then(() => 'error' as const),
  ]);

  if (result === 'error' && targetStatus !== 'error') {
    throw new Error(`Book processing failed: status changed to "error" on backend`);
  }
}
