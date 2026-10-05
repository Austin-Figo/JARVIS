/// <reference types="vite/client" />

interface JarvisConfig {
  apiBaseUrl?: string;
}

interface Window {
  __JARVIS_CONFIG__?: JarvisConfig;
}