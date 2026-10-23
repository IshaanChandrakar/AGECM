import { defineConfig } from '@playwright/test';
export default defineConfig({testDir:'./tests',timeout:30000,use:{baseURL:process.env.E2E_BASE_URL||'http://127.0.0.1:5183',headless:true,launchOptions:{channel:'chrome'}},reporter:'list',workers:1});
