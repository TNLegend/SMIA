import React, { useEffect, useState } from 'react';
import {
  Grid,
  Typography,
  Box,
  Button,
  useTheme,
  CircularProgress,
} from '@mui/material';
import {
  BrainCircuit,
  AlertTriangle,
  FileText,
  ShieldCheck,
  Lock,
} from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import LineChart from '../components/charts/LineChart';
import ProjectCard from '../components/projects/ProjectCard';
import { useApi } from '../api/client';
import { useTeam } from '../context/TeamContext';

interface ComplianceDetail {
  project_id: number;
  project_title: string;
  description?: string;
  category?: string;
  owner?: string;
  createdAt?: string;
  status?: 'active' | 'completed' | 'on-hold';
  riskLevel?: 'low' | 'medium' | 'high';
  compliance_score: number;
  total_questions: number;
  conform_questions: number;
}

interface EvaluationSummary {
  project_id: number;
  project_title: string;
  evaluation_date: string | null;
  status: string;
  metrics: Record<string, any>;
}

interface RecentComment {
  comment_id: string;
  project_id: number;
  author: string;
  content: string;
  date: string;
}

interface DashboardData {
  team_id: number;
  team_name: string;
  total_projects: number;
  average_compliance_iso42001: number;
  compliance_details: ComplianceDetail[];
  major_nonconformities_count: number;
  open_actions_correctives_count: number;
  evaluations: EvaluationSummary[];
  recent_comments: RecentComment[];
}

const Dashboard = () => {
  const theme = useTheme();
  const api = useApi();
  const { teamId } = useTeam();

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!teamId) return;

    setLoading(true);
    api(`/teams/${teamId}/dashboard/full_summary`)
      .then(res => {
        if (!res.ok) throw new Error('Erreur lors du chargement du dashboard');
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [teamId, api]);

  if (loading)
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 6 }}>
        <CircularProgress />
      </Box>
    );
  if (error) return <Typography color="error">{error}</Typography>;
  if (!data) return null;

  // Calcul des totaux pour les pourcentages
  const totalQuestions = data.compliance_details.reduce(
    (acc, proj) => acc + proj.total_questions,
    0
  );

  // Calcul % non-conformités majeures (par rapport au total des questions)
  const majorNcPercentage = totalQuestions > 0
    ? Number(((data.major_nonconformities_count / totalQuestions) * 100).toFixed(3))
    : 0;

  // Calcul % actions correctives ouvertes (par rapport au total des questions)
  const openActionsPercentage = totalQuestions > 0
    ? Number(((data.open_actions_correctives_count / totalQuestions) * 100).toFixed(3))
    : 0;

  // Préparer données graphiques conformité par projet
  const complianceLabels = data.compliance_details.map(p => p.project_title);
const complianceScores = data.compliance_details.map(p => 
  Number(p.compliance_score.toFixed(2))
);
  return (
    <Box>
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="h4" fontWeight={700}>
          Tableau de bord
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Statistiques principales */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Projets IA"
            value={data.total_projects.toString()}
            icon={<BrainCircuit size={20} />}
            color={theme.palette.primary.main}
            percentage={100}
            trend="up"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Non-conformités majeures"
            value={data.major_nonconformities_count.toString()}
            icon={<AlertTriangle size={20} />}
            color={theme.palette.error.main}
            percentage={majorNcPercentage}
            trend={data.major_nonconformities_count > 0 ? 'down' : 'up'}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Conformité ISO 42001"
            value={`${data.average_compliance_iso42001}%`}
            icon={<ShieldCheck size={20} />}
            color={theme.palette.success.main}
            percentage={data.average_compliance_iso42001}
            progressType="circular"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Actions correctives ouvertes"
            value={data.open_actions_correctives_count.toString()}
            icon={<Lock size={20} />}
            color={theme.palette.secondary.main}
            percentage={openActionsPercentage}
            trend={data.open_actions_correctives_count > 0 ? 'down' : 'neutral'}
          />
        </Grid>

        {/* Graphique conformité par projet */}
        <Grid item xs={12} md={12}>
          <LineChart
  title="Conformité ISO 42001 par projet"
  labels={complianceLabels}
  datasets={[
    {
      label: 'Score conformité (%)',
      data: complianceScores,
      color: theme.palette.primary.main,
    },
  ]}
  height={320}
/>

        </Grid>

        {/* Projets récents */}
        <Grid item xs={12}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Projets récents
          </Typography>
          <Grid container spacing={3}>
            {data.compliance_details.map(project => (
              <Grid item xs={12} sm={6} md={4} key={project.project_id}>
                <ProjectCard
                  id={project.project_id.toString()}
                  title={project.project_title}
                  description={project.description || ''}
                  category={project.category || 'Non défini'}
                  owner={project.owner || 'Inconnu'}
                  createdAt={project.createdAt || ''}
                  status={project.status || 'active'}
                  riskLevel={project.riskLevel || 'medium'}
                  complianceScore={project.compliance_score}
                />
              </Grid>
            ))}
          </Grid>
        </Grid>

        {/* Commentaires récents */}
        <Grid item xs={12}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Commentaires récents
          </Typography>
          {data.recent_comments.length === 0 && (
            <Typography>Aucun commentaire récent</Typography>
          )}
          {data.recent_comments.map(c => (
            <Box
              key={c.comment_id}
              sx={{
                mb: 2,
                p: 2,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 2,
              }}
            >
              <Typography variant="subtitle2" fontWeight={600}>
                {c.author}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(c.date).toLocaleString()}
              </Typography>
              <Typography variant="body1">{c.content}</Typography>
            </Box>
          ))}
        </Grid>


{/* Dernières évaluations (listing simple amélioré) */}
<Grid item xs={12}>
  <Typography variant="h5" fontWeight={600} gutterBottom>
    Dernières évaluations IA
  </Typography>

  {data.evaluations.length === 0 && (
    <Typography>Aucune évaluation</Typography>
  )}

  {data.evaluations.slice(0, 5).map((evalItem) => {
    // ─── 1. Pick des métriques « importantes » ────────────────────
    //   (le back range tout dans metrics.performance)
    const perf = evalItem.metrics?.performance ?? {};
    const isReg = 'r2' in perf || 'mse' in perf;

    // Sélectionne les clés d’intérêt
    const wantedKeys = isReg
      ? ['r2', 'mse']
      : ['accuracy', 'f1', 'auc'];      // auc ou auc_ovr selon le cas
    const displayMetrics = wantedKeys
      .filter((k) => perf[k] !== undefined)
      .map((k) => [k, perf[k]] as [string, number]);

    return (
      <Box
        key={evalItem.project_id}
        sx={{
          mb: 2,
          p: 2,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
        }}
      >
        {/* ─── En-tête projet + statut ───────────────────────────── */}
        <Typography variant="subtitle1" fontWeight={600}>
          {evalItem.project_title} — {evalItem.status}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Date&nbsp;:&nbsp;
          {evalItem.evaluation_date
            ? new Date(evalItem.evaluation_date).toLocaleString()
            : 'Non évalué'}
        </Typography>

        {/* ─── Tableau/ligne des métriques clés ─────────────────── */}
        {displayMetrics.length > 0 && (
          <Box sx={{ mt: 1, ml: 1 }}>
            {displayMetrics.map(([k, v]) => (
              <Typography key={k} variant="body2">
                <strong>{k.toUpperCase()} :</strong>{' '}
                {/* Formate : % pour accuracy/F1/AUC, 4 déc. sinon */}
                {['accuracy', 'f1', 'auc'].includes(k)
                  ? `${(v * 100).toFixed(2)} %`
                  : v.toFixed(4)}
              </Typography>
            ))}
          </Box>
        )}
      </Box>
    );
  })}
</Grid>



      </Grid>
    </Box>
  );
};

export default Dashboard;
