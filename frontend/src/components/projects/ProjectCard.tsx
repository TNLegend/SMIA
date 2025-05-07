import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  ButtonBase
} from '@mui/material';
import { 
  MoreVertical, 
  Edit, 
  Trash, 
  Eye, 
  AlertTriangle, 
  CheckCircle,
  ShieldAlert,
  FileText
} from 'lucide-react';

export interface ProjectCardProps {
  id: string;
  title: string;
  description: string;
  category: string;
  owner: string;
  createdAt: string;
  status: 'active' | 'completed' | 'on-hold';
  riskLevel: 'low' | 'medium' | 'high';
  complianceScore: number;
}

const ProjectCard = ({
  id,
  title,
  description,
  category,
  owner,
  createdAt,
  status,
  riskLevel,
  complianceScore
}: ProjectCardProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };
  
  const handleClose = () => {
    setAnchorEl(null);
  };
  
  const handleViewDetails = () => {
    navigate(`/projects/${id}`);
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main;
      case 'completed':
        return theme.palette.primary.main;
      case 'on-hold':
        return theme.palette.warning.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return theme.palette.success.main;
      case 'medium':
        return theme.palette.warning.main;
      case 'high':
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const getComplianceColor = (score: number) => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };
  
  const getRiskIcon = (risk: string): JSX.Element | undefined => {
    switch (risk) {
      case 'low':
        return <CheckCircle size={16} />;
      case 'medium':
        return <AlertTriangle size={16} />;
      case 'high':
        return <ShieldAlert size={16} />;
      
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
    >
      <ButtonBase 
        component="div" 
        onClick={handleViewDetails}
        sx={{ 
          display: 'block', 
          textAlign: 'initial',
          height: '100%' 
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100%',
            height: '4px',
            backgroundColor: getComplianceColor(complianceScore),
          }}
        />
        
        <CardContent sx={{ pb: 1, flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Chip 
              label={category} 
              size="small" 
              sx={{ 
                borderRadius: '4px',
                backgroundColor: theme.palette.primary.main,
                color: '#fff',
                fontWeight: 500,
                fontSize: '0.7rem',
              }} 
            />
            <Tooltip title="Options" onClick={(e) => e.stopPropagation()}>
              <IconButton 
                size="small" 
                onClick={handleClick}
                sx={{ mr: -1 }}
              >
                <MoreVertical size={18} />
              </IconButton>
            </Tooltip>
          </Box>
          
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              mb: 1, 
              fontWeight: 600,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 1,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {title}
          </Typography>
          
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              mb: 2,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              height: '40px',
            }}
          >
            {description}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 1 }}>
            <Chip 
              label={status} 
              size="small" 
              sx={{ 
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.1)' 
                  : 'rgba(0, 0, 0, 0.1)',
                color: getStatusColor(status),
                fontWeight: 500,
                fontSize: '0.7rem',
                borderRadius: '4px',
                '& .MuiChip-label': {
                  px: 1,
                }
              }} 
            />
            
            <Chip 
              icon={getRiskIcon(riskLevel)}
              label={`Risque ${riskLevel}`} 
              size="small" 
              sx={{ 
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.1)' 
                  : 'rgba(0, 0, 0, 0.1)',
                color: getRiskColor(riskLevel),
                fontWeight: 500,
                fontSize: '0.7rem',
                borderRadius: '4px',
                '& .MuiChip-label': {
                  px: 1,
                },
                '& .MuiChip-icon': {
                  color: getRiskColor(riskLevel),
                },
              }} 
            />
          </Box>
          
          <Typography variant="caption" sx={{ display: 'block', mb: 1 }}>
            Responsable: {owner}
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption">Conformité</Typography>
              <Typography variant="caption" fontWeight={500}>
                {complianceScore}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={complianceScore} 
              sx={{ 
                height: 6,
                borderRadius: 5,
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.1)' 
                  : 'rgba(0, 0, 0, 0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: getComplianceColor(complianceScore),
                  borderRadius: 5,
                }
              }}
            />
          </Box>
          
          <Typography 
            variant="caption" 
            color="text.secondary" 
            sx={{ 
              display: 'block', 
              mt: 2,
              textAlign: 'right' 
            }}
          >
            Créé le {createdAt}
          </Typography>
        </CardContent>
      </ButtonBase>
      
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        onClick={(e) => e.stopPropagation()}
        PaperProps={{
          sx: {
            boxShadow: theme.shadows[3],
            mt: 1.5,
            minWidth: 180,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => { handleClose(); handleViewDetails(); }}>
          <ListItemIcon>
            <Eye size={18} />
          </ListItemIcon>
          <ListItemText>Voir les détails</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleClose}>
          <ListItemIcon>
            <Edit size={18} />
          </ListItemIcon>
          <ListItemText>Modifier</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleClose}>
          <ListItemIcon>
            <FileText size={18} />
          </ListItemIcon>
          <ListItemText>Générer rapport</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleClose} sx={{ color: theme.palette.error.main }}>
          <ListItemIcon sx={{ color: theme.palette.error.main }}>
            <Trash size={18} />
          </ListItemIcon>
          <ListItemText>Supprimer</ListItemText>
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default ProjectCard;