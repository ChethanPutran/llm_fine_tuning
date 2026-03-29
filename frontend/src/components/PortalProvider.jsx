// src/components/PortalProvider.jsx
import React from 'react';
import { createPortal } from 'react-dom';

export const PortalContext = React.createContext(null);

export const PortalProvider = ({ children }) => {
  const [portalContainer, setPortalContainer] = React.useState(null);
  
  React.useEffect(() => {
    // Wait for DOM to be ready
    const container = document.getElementById('modal-root');
    setPortalContainer(container);
  }, []);
  
  if (!portalContainer) {
    return null; // Don't render until portal container exists
  }
  
  return (
    <PortalContext.Provider value={portalContainer}>
      {children}
      {createPortal(<div id="mui-portal-placeholder" />, portalContainer)}
    </PortalContext.Provider>
  );
};