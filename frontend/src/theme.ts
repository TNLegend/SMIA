import { createTheme, PaletteMode } from '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Palette {
    tertiary: Palette['primary'];
  }
  interface PaletteOptions {
    tertiary?: PaletteOptions['primary'];
  }
}

export const theme = (mode: PaletteMode | boolean) => {
  const isDark = mode === true || mode === 'dark';
  
  return createTheme({
    palette: {
      mode: isDark ? 'dark' : 'light',
      primary: {
        main: '#4361EE',
        light: '#4CC9F0',
        dark: '#3A0CA3',
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: '#7209B7',
        light: '#9D4EDD',
        dark: '#560BAD',
        contrastText: '#FFFFFF',
      },
      tertiary: {
        main: '#4CC9F0',
        light: '#90E0EF',
        dark: '#0077B6',
        contrastText: isDark ? '#FFFFFF' : '#0A1128',
      },
      background: {
        default: isDark ? '#0A1128' : '#F7F9FC',
        paper: isDark ? '#0F1A40' : '#FFFFFF',
      },
      success: {
        main: '#06D6A0',
        light: '#2CEAA3',
        dark: '#058C67',
      },
      error: {
        main: '#E63946',
        light: '#FF5A67',
        dark: '#B02A35',
      },
      warning: {
        main: '#F7B801',
        light: '#FFCF33',
        dark: '#C49000',
      },
      text: {
        primary: isDark ? '#F7F9FC' : '#0A1128',
        secondary: isDark ? '#CCD6F6' : '#4A5568',
      },
    },
    typography: {
      fontFamily: '"SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
        lineHeight: 1.2,
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        lineHeight: 1.2,
      },
      h3: {
        fontSize: '1.75rem',
        fontWeight: 600,
        lineHeight: 1.2,
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 500,
        lineHeight: 1.2,
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 500,
        lineHeight: 1.2,
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 500,
        lineHeight: 1.2,
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
        fontWeight: 500,
        textTransform: 'none',
      },
    },
    shape: {
      borderRadius: 10,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            padding: '10px 16px',
            boxShadow: 'none',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: isDark 
                ? '0 6px 20px rgba(67, 97, 238, 0.3)'
                : '0 6px 20px rgba(67, 97, 238, 0.15)',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            boxShadow: isDark 
              ? '0 10px 30px -10px rgba(2, 12, 27, 0.7)'
              : '0 10px 30px -10px rgba(2, 12, 27, 0.1)',
            transition: 'all 0.3s ease-in-out',
            '&:hover': {
              transform: 'translateY(-5px)',
              boxShadow: isDark 
                ? '0 20px 30px -15px rgba(2, 12, 27, 0.7)'
                : '0 20px 30px -15px rgba(2, 12, 27, 0.1)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
    },
  });
};