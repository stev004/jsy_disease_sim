import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import './styles/tokens.css';
import './styles/base.css';
import './styles/views.css';

import { primeClient } from './api';
import { ToastProvider } from './components/Toast';
import { DetailProvider } from './app/DetailProvider';
import { DrawerProvider } from './app/Drawer';
import { ScenarioContextProvider } from './app/ScenarioContextProvider';
import { ThemeProvider } from './app/ThemeProvider';
import { AppRoutes } from './app/routes';

// Decide real-API vs. mock as early as possible.
primeClient();

const container = document.getElementById('root');
if (!container) throw new Error('#root not found');

createRoot(container).render(
  <StrictMode>
    <ThemeProvider>
      <DetailProvider>
        <ToastProvider>
          <ScenarioContextProvider>
            <BrowserRouter>
              <DrawerProvider>
                <AppRoutes />
              </DrawerProvider>
            </BrowserRouter>
          </ScenarioContextProvider>
        </ToastProvider>
      </DetailProvider>
    </ThemeProvider>
  </StrictMode>,
);
