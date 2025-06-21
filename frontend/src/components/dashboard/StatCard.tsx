import { ReactNode } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  LinearProgress, 
  CircularProgress, 
  useTheme 
} from '@mui/material';
import { DivideIcon as LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color: string;
  percentage?: number;
  trend?: 'up' | 'down' | 'neutral';
  loading?: boolean;
  progressType?: 'linear' | 'circular';
}

const StatCard = ({
  title,
  value,
  icon,
  color,
  percentage,
  trend,
  loading = false,
  progressType = 'linear'
}: StatCardProps) => {
  const theme = useTheme();
  
  return (
    <Card
      sx={{
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        '&:before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '6px',
          height: '100%',
          backgroundColor: color,
          borderTopLeftRadius: theme.shape.borderRadius,
          borderBottomLeftRadius: theme.shape.borderRadius,
        },
      }}
    >
      <CardContent sx={{ height: '100%', pl: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography 
            variant="subtitle2" 
            color="text.secondary"
            sx={{ fontWeight: 500 }}
          >
            {title}
          </Typography>
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: color,
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.05)' 
                : 'rgba(0, 0, 0, 0.05)',
              borderRadius: '50%',
              width: 36,
              height: 36
            }}
          >
            {icon}
          </Box>
        </Box>
        
        {loading ? (
          <Box sx={{ my: 3, display: 'flex', justifyContent: 'center' }}>
            <CircularProgress size={24} thickness={4} />
          </Box>
        ) : (
          <Typography 
            variant="h4" 
            component="div" 
            sx={{ 
              mb: 1, 
              fontWeight: 700,
              color: theme.palette.text.primary 
            }}
          >
            {value}
          </Typography>
        )}
        
        {percentage !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, mb: 0.5 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                color: trend === 'up' 
                  ? theme.palette.success.main 
                  : trend === 'down' 
                    ? theme.palette.error.main 
                    : theme.palette.text.secondary,
                display: 'flex',
                alignItems: 'center',
                fontWeight: 500
              }}
            >
              {percentage}%
              {trend && (
                <Box 
                  component="span" 
                  sx={{ 
                    ml: 0.5,
                    display: 'flex',
                    alignItems: 'center' 
                  }}
                >
                  {trend === 'up' ? '↑' : trend === 'down' ? '↓' : ''}
                </Box>
              )}
            </Typography>
          </Box>
        )}
        
        {progressType === 'linear' && percentage !== undefined && (
          <LinearProgress 
            variant="determinate" 
            value={percentage} 
            sx={{ 
              mt: 1,
              height: 6,
              borderRadius: 5,
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.1)' 
                : 'rgba(0, 0, 0, 0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: color,
                borderRadius: 5,
              }
            }} 
          />
        )}

        {progressType === 'circular' && percentage !== undefined && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
            <CircularProgress 
              variant="determinate" 
              value={percentage} 
              size={50}
              thickness={4}
              sx={{ 
                color: color,
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                },
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StatCard;