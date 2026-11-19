import { test as base, expect } from '@playwright/test';

type Fixtures = {
  apiBase: string;
};

export const test = base.extend<Fixtures>({
  apiBase: async ({}, use) => {
    await use(process.env.API_URL ?? 'http://localhost:8000');
  },
});

export { expect };
