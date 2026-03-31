import { createTheme } from '@mui/material/styles';

// Modern color palette
const colors = {
  // Primary colors - Modern blue/purple gradient
  primary: {
    light: '#6366f1',
    main: '#4f46e5',
    dark: '#4338ca',
    contrast: '#ffffff',
  },
  // Secondary colors - Modern pink/rose
  secondary: {
    light: '#f472b6',
    main: '#ec489a',
    dark: '#db2777',
    contrast: '#ffffff',
  },
  // Success colors - Modern green
  success: {
    light: '#4ade80',
    main: '#22c55e',
    dark: '#16a34a',
    contrast: '#ffffff',
  },
  // Error colors - Modern red
  error: {
    light: '#f87171',
    main: '#ef4444',
    dark: '#dc2626',
    contrast: '#ffffff',
  },
  // Warning colors - Modern amber
  warning: {
    light: '#fbbf24',
    main: '#f59e0b',
    dark: '#d97706',
    contrast: '#1f2937',
  },
  // Info colors - Modern sky
  info: {
    light: '#38bdf8',
    main: '#0ea5e9',
    dark: '#0284c7',
    contrast: '#ffffff',
  },
  // Gray scale
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
};

// Modern gradients
const gradients = {
  primary: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
  secondary: 'linear-gradient(135deg, #f472b6 0%, #ec489a 100%)',
  success: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
  error: 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)',
  warning: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
  info: 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%)',
  dark: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
};

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: colors.primary,
    secondary: colors.secondary,
    success: colors.success,
    error: colors.error,
    warning: colors.warning,
    info: colors.info,
    grey: colors.gray,
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
      subtle: '#f1f5f9',
    },
    text: {
      primary: '#0f172a',
      secondary: '#475569',
      disabled: '#94a3b8',
      hint: '#64748b',
    },
    divider: '#e2e8f0',
    action: {
      active: '#4f46e5',
      hover: 'rgba(79, 70, 229, 0.04)',
      selected: 'rgba(79, 70, 229, 0.08)',
      disabled: 'rgba(0, 0, 0, 0.26)',
      disabledBackground: 'rgba(0, 0, 0, 0.12)',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '3.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      background: gradients.primary,
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      color: 'transparent',
    },
    h2: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 600,
      textTransform: 'none',
      letterSpacing: '0.3px',
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.5,
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0, 0, 0, 0.05)',
    '0px 4px 6px rgba(0, 0, 0, 0.05)',
    '0px 6px 8px rgba(0, 0, 0, 0.05)',
    '0px 8px 12px rgba(0, 0, 0, 0.05)',
    '0px 10px 14px rgba(0, 0, 0, 0.05)',
    '0px 12px 16px rgba(0, 0, 0, 0.05)',
    '0px 14px 18px rgba(0, 0, 0, 0.05)',
    '0px 16px 20px rgba(0, 0, 0, 0.05)',
    '0px 18px 22px rgba(0, 0, 0, 0.05)',
    '0px 20px 24px rgba(0, 0, 0, 0.05)',
    '0px 22px 26px rgba(0, 0, 0, 0.05)',
    '0px 24px 28px rgba(0, 0, 0, 0.05)',
    '0px 26px 30px rgba(0, 0, 0, 0.05)',
    '0px 28px 32px rgba(0, 0, 0, 0.05)',
    '0px 30px 34px rgba(0, 0, 0, 0.05)',
    '0px 32px 36px rgba(0, 0, 0, 0.05)',
    '0px 34px 38px rgba(0, 0, 0, 0.05)',
    '0px 36px 40px rgba(0, 0, 0, 0.05)',
    '0px 38px 42px rgba(0, 0, 0, 0.05)',
    '0px 40px 44px rgba(0, 0, 0, 0.05)',
    '0px 42px 46px rgba(0, 0, 0, 0.05)',
    '0px 44px 48px rgba(0, 0, 0, 0.05)',
    '0px 46px 50px rgba(0, 0, 0, 0.05)',
    '0px 48px 52px rgba(0, 0, 0, 0.05)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollBehavior: 'smooth',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#f1f1f1',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#c1c1c1',
            borderRadius: '4px',
            '&:hover': {
              background: '#a8a8a8',
            },
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: '10px',
          padding: '8px 20px',
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          },
        },
        contained: {
          background: gradients.primary,
          color: '#ffffff',
          '&:hover': {
            background: gradients.primary,
            filter: 'brightness(1.05)',
          },
        },
        outlined: {
          borderWidth: '2px',
          '&:hover': {
            borderWidth: '2px',
          },
        },
        sizeLarge: {
          padding: '12px 28px',
          fontSize: '1rem',
        },
        sizeSmall: {
          padding: '6px 16px',
          fontSize: '0.8125rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          boxShadow: '0 4px 6px -2px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 12px 24px -8px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          transition: 'all 0.3s ease',
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
        },
        elevation2: {
          boxShadow: '0 4px 6px -2px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        },
        elevation3: {
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: gradients.primary,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRadius: '0',
          borderRight: 'none',
          boxShadow: '4px 0 12px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '10px',
            transition: 'all 0.2s ease',
            '&:hover': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: colors.primary.main,
              },
            },
            '&.Mui-focused': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderWidth: '2px',
                borderColor: colors.primary.main,
              },
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          fontWeight: 500,
        },
        colorPrimary: {
          background: gradients.primary,
          color: '#ffffff',
        },
        colorSecondary: {
          background: gradients.secondary,
          color: '#ffffff',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          border: 'none',
        },
        standardSuccess: {
          background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
          color: '#166534',
        },
        standardError: {
          background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
          color: '#991b1b',
        },
        standardWarning: {
          background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
          color: '#92400e',
        },
        standardInfo: {
          background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
          color: '#1e40af',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.875rem',
          minHeight: '48px',
          '&.Mui-selected': {
            color: colors.primary.main,
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          background: gradients.primary,
          height: '3px',
          borderRadius: '3px',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
          height: '8px',
        },
        bar: {
          borderRadius: '10px',
          background: gradients.primary,
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          background: gradients.primary,
          color: '#ffffff',
          '&:hover': {
            background: gradients.primary,
            filter: 'brightness(1.05)',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: '8px',
          fontSize: '0.75rem',
          fontWeight: 500,
          padding: '6px 12px',
          backgroundColor: colors.gray[900],
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: '20px',
          padding: '8px',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          margin: '4px 8px',
          '&:hover': {
            backgroundColor: 'rgba(79, 70, 229, 0.08)',
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          margin: '2px 8px',
          '&:hover': {
            backgroundColor: 'rgba(79, 70, 229, 0.08)',
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(79, 70, 229, 0.12)',
            '&:hover': {
              backgroundColor: 'rgba(79, 70, 229, 0.16)',
            },
          },
        },
      },
    },
  },
});

export const darkTheme = createTheme({
  ...lightTheme,
  palette: {
    mode: 'dark',
    primary: colors.primary,
    secondary: colors.secondary,
    success: colors.success,
    error: colors.error,
    warning: colors.warning,
    info: colors.info,
    grey: colors.gray,
    background: {
      default: '#0f172a',
      paper: '#1e293b',
      subtle: '#334155',
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#cbd5e1',
      disabled: '#64748b',
      hint: '#94a3b8',
    },
    divider: '#334155',
    action: {
      active: '#6366f1',
      hover: 'rgba(99, 102, 241, 0.08)',
      selected: 'rgba(99, 102, 241, 0.16)',
      disabled: 'rgba(255, 255, 255, 0.3)',
      disabledBackground: 'rgba(255, 255, 255, 0.12)',
    },
  },
  components: {
    ...lightTheme.components,
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollBehavior: 'smooth',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#1e293b',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#475569',
            borderRadius: '4px',
            '&:hover': {
              background: '#64748b',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        standardSuccess: {
          background: 'linear-gradient(135deg, #022c22 0%, #064e3b 100%)',
          color: '#6ee7b7',
        },
        standardError: {
          background: 'linear-gradient(135deg, #450a0a 0%, #7f1a1a 100%)',
          color: '#fca5a5',
        },
        standardWarning: {
          background: 'linear-gradient(135deg, #451a03 0%, #78350f 100%)',
          color: '#fdba74',
        },
        standardInfo: {
          background: 'linear-gradient(135deg, #082f49 0%, #0c4a6e 100%)',
          color: '#7dd3fc',
        },
      },
    },
  },
});

// Add custom global styles
export const globalStyles = {
  '@keyframes fadeIn': {
    from: {
      opacity: 0,
      transform: 'translateY(10px)',
    },
    to: {
      opacity: 1,
      transform: 'translateY(0)',
    },
  },
  '@keyframes slideIn': {
    from: {
      transform: 'translateX(-20px)',
      opacity: 0,
    },
    to: {
      transform: 'translateX(0)',
      opacity: 1,
    },
  },
  '@keyframes pulse': {
    '0%, 100%': {
      opacity: 1,
    },
    '50%': {
      opacity: 0.5,
    },
  },
  '@keyframes shimmer': {
    '0%': {
      backgroundPosition: '-1000px 0',
    },
    '100%': {
      backgroundPosition: '1000px 0',
    },
  },
};