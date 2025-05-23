// src/components/EvaluationRisksFR.tsx
import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  SyntheticEvent,
} from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Divider,
  CircularProgress,
  Typography,
  useTheme,
  Grid,
  Card,
  CardContent,
  Chip,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableSortLabel,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  Balance as BalanceIcon,
  BarChart as BarChartIcon,
  Group as GroupIcon,
  BubbleChart as ExplainIcon,
} from '@mui/icons-material';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useParams } from 'react-router-dom';
import { useApi } from '../api/client';


/* ───────────────────────── helpers et types ───────────────────────── */
const PCT_KEYS = ['accuracy', 'precision', 'recall', 'f1', 'auc'];

const fairnessAttributesFR: Record<string, string> = {
  feature_1: "Caractéristique 1",
  feature_2: "Caractéristique 2",
  feature_3: "Caractéristique 3",
  // ajoute ici d’autres si nécessaire
};

const fairnessMetricsFR: Record<string, string> = {
  statistical_parity_diff: "Différence\n de parité\n statistique",
  disparate_impact: "Impact disparate",
  equal_opportunity_diff: "Différence\n égalité\n des chances",
  predictive_parity_diff: "Différence\n de parité\n prédictive",
};

type PerformanceMetrics = Record<string, number | undefined>;
type FairnessMetrics = Record<string, Record<string, number>>;
type RobustnessMetrics = { prediction_variance?: number; adversarial?: Record<string, number> };
type DriftMetrics = { psi?: Record<string, number>; ks_drift?: { is_drift: boolean; p_value: number } };

interface Metrics {
  performance?: PerformanceMetrics;
  performance_by_group?: Record<string, { support?: number; accuracy?: number; f1?: number }>;
  fairness?: FairnessMetrics;
  fairness_intersectional?: Record<string, { support?: number; accuracy?: number; positive_rate?: number }>;
  drift?: DriftMetrics;
  robustness?: RobustnessMetrics;
  explainability?: Record<string, any>;
  clustering?: { silhouette: number };
}

/* ─────────────────────────── composant ───────────────────────────── */
export default function EvaluationRisks() {
  const theme = useTheme();
  const { id: projectId } = useParams<{ id: string }>();
  const api = useApi();

  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
  const [plotUrls, setPlotUrls] = useState<Record<string, string>>({});
  const prevPlotUrls = useRef<Record<string, string>>({});
  const driftColors = ['#FF6F61', '#6B8E23', '#FFA500', '#DAA520', '#CD5C5C', '#8FBC8F'];
  const robustnessColors = ['#FF8C00', '#9ACD32', '#FF4500', '#D2691E', '#FF6347', '#228B22'];
  const MultilineTick = (props: any) => {
  const { x, y, payload } = props;
  const lines = payload.value.split('\n');
  const lineHeight = 14; // espace vertical entre les lignes
  const topMargin = 15;  // marge en pixels au-dessus des labels

  return (
    <g transform={`translate(${x},${y + topMargin})`}>  {/* Décale tout le groupe vers le bas */}
      {lines.map((line: string, index: number) => (
        <text
          key={index}
          x={0}
          y={index * lineHeight}
          dy={0}
          textAnchor="middle"
          fontSize={12}
          fill="#666"
        >
          {line}
        </text>
      ))}
    </g>
  );
};


  /* ─── 1) récupérer la dernière évaluation ─────────────────────── */
  useEffect(() => {
    const ctrl = new AbortController();
    let mounted = true;

    (async () => {
      try {
        setLoading(true);
        const listRes = await api(`/projects/${projectId}/evaluations`, { signal: ctrl.signal });
        if (!listRes.ok) throw new Error(`Échec de la liste (${listRes.status})`);
        const arr = await listRes.json();
        if (!arr.length) throw new Error('Aucune évaluation pour le moment');

        const latest = arr[arr.length - 1];
        const detRes = await api(`/projects/${projectId}/evaluations/${latest.id}`, { signal: ctrl.signal });
        if (!detRes.ok) throw new Error(`Échec du détail (${detRes.status})`);
        if (mounted) {
          setRunId(latest.id);
          setMetrics((await detRes.json()).metrics as Metrics);
        }
      } catch (e: any) {
        if (mounted && e.name !== 'AbortError') setError(e.message);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
      ctrl.abort();
    };
  }, [projectId]);

  /* ─── 2) récupérer les graphiques d'explicabilité ─────────────── */
  useEffect(() => {
    if (!runId || !metrics?.explainability) return;
    let mounted = true;

    (async () => {
      const urls: Record<string, string> = {};
      for (const key of Object.keys(metrics.explainability!)) {
        if (!key.endsWith('_plot')) continue;
        const name = key.replace('_plot', '');
        try {
          const res = await api(`/projects/${projectId}/evaluations/${runId}/plots/${name}`);
          if (!res.ok) continue;
          const blob = await res.blob();
          urls[name] = URL.createObjectURL(blob);
        } catch {
          /* ignore */
        }
      }
      if (mounted) {
        Object.values(prevPlotUrls.current).forEach(URL.revokeObjectURL);
        prevPlotUrls.current = urls;
        setPlotUrls(urls);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [projectId, runId, metrics?.explainability]);

  /* ─── transformations ─────────────────────────────────────────── */
  const radarData = useMemo(() => {
    if (!metrics?.performance) return [];
    return PCT_KEYS.filter(k => metrics.performance![k] != null).map(k => ({
      subject: k.toUpperCase(),
      value: metrics.performance![k]! * 100,
    }));
  }, [metrics?.performance]);

  const barPerfData = useMemo(() => {
    if (!metrics?.performance) return [];
    return Object.entries(metrics.performance!)
      .filter(([k, v]) => v != null && !PCT_KEYS.includes(k))
      .map(([k, v]) => ({ metric: k.toUpperCase(), value: v! }));
  }, [metrics?.performance]);

  const fairnessBarData = useMemo(() => {
    if (!metrics?.fairness) return [];
    return Object.entries(metrics.fairness).map(([attr, vals]) => ({
      attribute: fairnessAttributesFR[attr] ?? attr,
      data: Object.entries(vals).map(([m, v]) => ({
        metric: fairnessMetricsFR[m] ?? m.toUpperCase(),
        value: v,
      })),
    }));
  }, [metrics?.fairness]);

  const psiData = useMemo(
    () =>
      metrics?.drift?.psi
        ? Object.entries(metrics.drift.psi!).map(([f, v]) => ({ name: f, value: v }))
        : [],
    [metrics?.drift],
  );

  const advData = useMemo(
    () =>
      metrics?.robustness?.adversarial
        ? Object.entries(metrics.robustness.adversarial!).map(([m, v]) => ({ name: m.toUpperCase(), value: v }))
        : [],
    [metrics?.robustness],
  );

  const silhouette = metrics?.clustering?.silhouette ?? 0;
  const silhouetteData = [
    { name: 'Score', value: silhouette * 100 },
    { name: 'Reste', value: 100 - silhouette * 100 },
  ];
  const COLORS = [theme.palette.primary.main, theme.palette.divider];

  const groupPerfRows = useMemo(() => {
    if (!metrics?.performance_by_group) return [];
    return Object.entries(metrics.performance_by_group!).map(([g, v]) => ({
      group: g,
      accuracy: v.accuracy != null ? v.accuracy * 100 : undefined,
      f1: v.f1 != null ? v.f1 * 100 : undefined,
      support: v.support,
    }));
  }, [metrics?.performance_by_group]);

  const interRows = useMemo(() => {
    if (!metrics?.fairness_intersectional) return [];
    return Object.entries(metrics.fairness_intersectional!).map(([k, v]) => ({
      key: k,
      support: v.support,
      accuracy: v.accuracy != null ? v.accuracy * 100 : undefined,
      positive_rate: v.positive_rate != null ? v.positive_rate * 100 : undefined,
    }));
  }, [metrics?.fairness_intersectional]);

  const ready = !loading && !error && metrics;
  if (!ready) {
    return (
      <Box textAlign="center" py={10}>
        {loading ? <CircularProgress size={48} /> : <Typography color="error">{error || 'Aucune métrique trouvée'}</Typography>}
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3, bgcolor: theme.palette.background.default }} elevation={2}>
      {/* ─── Onglets ─────────────────────────────────────── */}
      <Tabs
        value={tab}
        onChange={(_: SyntheticEvent, v: number) => setTab(v)}
        variant="scrollable"
        scrollButtons="auto"
        textColor="primary"
        indicatorColor="primary"
        sx={{ mb: 3 }}
      >
        <Tab icon={<DashboardIcon />} label="Vue d'ensemble" />
        <Tab icon={<TrendingUpIcon />} label="Performance" />
        <Tab icon={<BalanceIcon />} label="Équité" />
        <Tab icon={<GroupIcon />} label="Perf. par groupe" />
        <Tab icon={<BarChartIcon />} label="Dérive & Robustesse" />
        <Tab icon={<ExplainIcon />} label="Explicabilité" />
      </Tabs>
      <Divider sx={{ mb: 3 }} />

      {/* ─── VUE D'ENSEMBLE ─────────────────────────────── */}
      {tab === 0 && (
        <Grid container spacing={3} sx={{ alignItems: 'stretch' }}>
          {metrics.performance?.r2 != null && (
            <Grid item xs>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography color="textSecondary">R²</Typography>
                  <Typography variant="h4">{metrics.performance.r2.toFixed(3)}</Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          {metrics.clustering?.silhouette != null && (
            <Grid item xs>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                  <Typography color="textSecondary">Silhouette</Typography>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={silhouetteData}
                        dataKey="value"
                        innerRadius={40}
                        outerRadius={60}
                        startAngle={90}
                        endAngle={-270}
                      >
                        {silhouetteData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i]} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <Typography variant="h6" sx={{ mt: 1 }}>
                    {(silhouette * 100).toFixed(1)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          {metrics.drift?.ks_drift && (
            <Grid item xs>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography color="textSecondary">Dérive KS</Typography>
                  <Chip
                    label={metrics.drift.ks_drift.is_drift ? 'Dérive' : 'Stable'}
                    color={metrics.drift.ks_drift.is_drift ? 'error' : 'success'}
                  />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    p = {metrics.drift.ks_drift.p_value.toFixed(3)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          {metrics.robustness?.prediction_variance != null && (
            <Grid item xs>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography color="textSecondary">Variance des prédictions</Typography>
                  <Typography variant="h5">{metrics.robustness.prediction_variance.toFixed(4)}</Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* ─── PERFORMANCE ────────────────────────────────── */}
      {tab === 1 && (
        <Box>
          {radarData.length > 0 && (
            <Box sx={{ width: '100%', height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} />
                  <Radar
                    dataKey="value"
                    name="%"
                    stroke={theme.palette.primary.main}
                    fill={theme.palette.primary.main}
                    fillOpacity={0.6}
                  />
                  <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
                </RadarChart>
              </ResponsiveContainer>
            </Box>
          )}
          {barPerfData.length > 0 && (
            <Box sx={{ mt: 4, width: '100%', height: 300 }}>
              <Typography variant="h6" gutterBottom>
                Autres métriques
              </Typography>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barPerfData}>
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip formatter={(v: number) => v.toFixed(3)} />
                  <Bar dataKey="value" fill={theme.palette.secondary.main} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          )}
        </Box>
      )}

      {/* ─── ÉQUITÉ ────────────────────────────────────── */}
      {tab === 2 &&
        (fairnessBarData.length > 0 ? (
          <Grid container spacing={2} sx={{ alignItems: 'stretch' }}>
            {fairnessBarData.map(({ attribute, data }) => (
              <Grid item xs key={attribute}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1, maxHeight: 1000, overflowY: 'auto' }}>
                    <Typography variant="subtitle1" gutterBottom>
                      {attribute}
                    </Typography>
                    <Box sx={{ width: '100%', height: 400 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                          <XAxis dataKey="metric" interval={0} height={60} tick={<MultilineTick />} />
                          <YAxis />
                          <Tooltip formatter={(v: number) => v.toFixed(2)} />
                          <Bar dataKey="value" fill={theme.palette.error.main} />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Typography textAlign="center" color="textSecondary">
            Aucune métrique d'équité.
          </Typography>
        ))}

     {/* ─── PERF. PAR GROUPE ─────────────────────────── */}
{tab === 3 && (
  <>
    {groupPerfRows.length > 0 ? (
      <Box sx={{ width: '100%', height: 500 /* augmenter la hauteur */ }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={groupPerfRows}
            margin={{ top: 10, right: 0, left: 0, bottom: 20 /* plus de marge en bas */ }}
          >
            <XAxis
              dataKey="group"
              interval={0}
              angle={-90}
              textAnchor="end"
              height={80} /* hauteur plus grande pour labels inclinés */
              tick={{ fontSize: 12 }}
            />
            <YAxis />
            <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
            <Legend verticalAlign="top" height={36} />
            <Bar dataKey="accuracy" name="Exactitude (%)" fill="#BA68C8" barSize={12} />
            <Bar dataKey="f1" name="F1 (%)" fill="#FFB74D" barSize={12} />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    ) : (
      <Typography textAlign="center" color="textSecondary">
        Aucune métrique au niveau des groupes.
      </Typography>
    )}
    {interRows.length > 0 && (
      <Box mt={4}>
        <Typography variant="h6" gutterBottom>
          Équité intersectionnelle
        </Typography>
        <SortableTable rows={interRows} />
      </Box>
    )}
  </>
)}

     {/* ─── DÉRIVE & ROBUSTESSE ───────────────────────── */}
{tab === 4 && (
  <Grid container spacing={2} alignItems="flex-start">
    {psiData.length > 0 && (
      <Grid item xs>
        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <CardContent sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle1" gutterBottom>
              Indice de stabilité de la population
            </Typography>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={psiData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v: number) => v.toFixed(2)} />
                <Bar dataKey="value">
                  {psiData.map((entry, index) => (
                    <Cell key={`cell-psi-${index}`} fill={driftColors[index % driftColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>
    )}
    {advData.length > 0 && (
      <Grid item xs>
        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <CardContent sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle1" gutterBottom>
              Robustesse adversariale
            </Typography>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={advData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v: number) => v.toFixed(3)} />
                <Bar dataKey="value">
                  {advData.map((entry, index) => (
                    <Cell key={`cell-adv-${index}`} fill={robustnessColors[index % robustnessColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>
    )}
    {!psiData.length && !advData.length && (
      <Typography sx={{ width: '100%' }} textAlign="center" color="textSecondary">
        Aucune métrique de dérive ou de robustesse.
      </Typography>
    )}
  </Grid>
)}

      {/* ─── EXPLICABILITÉ ─────────────────────────────── */}
      {tab === 5 && (
        <Grid container spacing={2} sx={{ alignItems: 'stretch' }}>
          {Object.keys(plotUrls).map(name => (
            <Grid item xs key={name}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ position: 'relative', pt: '75%' }}>
                  <Box
                    component="img"
                    src={plotUrls[name]}
                    alt={name}
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '260',
                      objectFit: 'contain',
                    }}
                  />
                </Box>
                <CardContent>
                  <Typography align="center" variant="subtitle2">
                    {name.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
          {!Object.keys(plotUrls).length && (
            <Typography sx={{ width: '100%', py: 4 }} textAlign="center" color="textSecondary">
              Aucun graphique d&apos;explicabilité.
            </Typography>
          )}
        </Grid>
      )}
    </Paper>
  );
}

/* ───────────────────────── helper de tableau ────────────────────── */
type Row = Record<string, any>;
function SortableTable({ rows }: { rows: Row[] }) {
  const [orderBy, setOrderBy] = useState<keyof Row>('key');
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(
    () =>
      [...rows].sort((a, b) => {
        const v1 = a[orderBy] ?? 0;
        const v2 = b[orderBy] ?? 0;
        return asc ? (v1 > v2 ? 1 : -1) : v1 < v2 ? 1 : -1;
      }),
    [rows, orderBy, asc],
  );

  return (
    <TableContainer component={Paper} elevation={0}>
      <Table size="small">
        <TableHead>
          <TableRow>
            {Object.keys(rows[0]).map(k => (
              <TableCell key={k}>
                <TableSortLabel
                  active={orderBy === k}
                  direction={orderBy === k && asc ? 'asc' : 'desc'}
                  onClick={() => {
                    setOrderBy(k as keyof Row);
                    setAsc(orderBy === k ? !asc : true);
                  }}
                >
                  {k.toUpperCase()}
                </TableSortLabel>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {sorted.map((row, i) => (
            <TableRow key={i}>
              {Object.keys(row).map(k => (
                <TableCell key={k}>{typeof row[k] === 'number' ? row[k].toFixed(2) : row[k]}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
