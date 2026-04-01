<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">My Analytics</h5>
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else class="row g-4">

      <!-- Personal funnel stat cards -->
      <div class="col-6 col-md-3" v-for="s in summaryCards" :key="s.label">
        <div class="card border-0 shadow-sm text-center stat-card h-100">
          <div class="card-body py-3">
            <div class="fs-2 fw-bold" :class="s.color">{{ s.value }}</div>
            <div class="text-muted small mt-1">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- Monthly application timeline line -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Application Activity (last 6 months)
          </div>
          <div class="card-body">
            <canvas ref="timelineChart" height="120"></canvas>
          </div>
        </div>
      </div>

      <!-- Status doughnut -->
      <div class="col-lg-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">Application Status</div>
          <div class="card-body d-flex align-items-center justify-content-center">
            <canvas ref="statusChart" height="200" style="max-height:240px"></canvas>
          </div>
        </div>
      </div>

      <!-- Skill gap analysis -->
      <div class="col-12">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white fw-semibold d-flex align-items-center gap-2">
            Skill Gap Analysis
            <span class="badge bg-info text-dark small">vs top 10 in-demand skills</span>
          </div>
          <div class="card-body">
            <canvas ref="skillGapChart" height="70"></canvas>
          </div>
          <div class="card-footer bg-white d-flex gap-3 small">
            <span><span class="badge bg-primary me-1">■</span>Market demand (# drives)</span>
            <span><span class="badge bg-success me-1">■</span>Your skills (you have it)</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import api from '../../api'
import { buildTrendLine, buildDoughnut, buildGroupedBar } from '../../utils/chartHelpers'

export default {
  name: 'StudentAnalyticsView',
  data() { return { loading: true, data: {}, charts: [] } },
  computed: {
    summaryCards() {
      const t = this.data.totals || {}
      return [
        { label: 'Applied',     value: t.applied     || 0, color: 'text-primary'   },
        { label: 'Shortlisted', value: t.shortlisted  || 0, color: 'text-info'      },
        { label: 'Placed',      value: t.placed       || 0, color: 'text-success'   },
        { label: 'Rejected',    value: t.rejected     || 0, color: 'text-danger'    },
      ]
    },
  },
  async mounted() {
    try {
      const { data } = await api.get('/analytics/student')
      this.data    = data
      this.loading = false
      this.$nextTick(() => this.buildCharts())
    } catch { this.loading = false }
  },
  beforeUnmount() { this.charts.forEach(c => c.destroy()) },
  methods: {
    buildCharts() {
      const d = this.data
      this.charts = [
        buildTrendLine(this.$refs.timelineChart, d.labels,
          [{ label: 'Applications', data: d.monthly_apps, color: '#0d6efd' }]),
        buildDoughnut(this.$refs.statusChart,
          Object.keys(d.status_counts  || {}),
          Object.values(d.status_counts || {})),
        buildGroupedBar(this.$refs.skillGapChart,
          d.skill_match?.labels || [],
          [{ label: 'Market demand', data: d.skill_match?.demand || [], color: '#0d6efd' },
           { label: 'You have it',   data: d.skill_match?.has    || [], color: '#198754' }]),
      ].filter(Boolean)
    },
  },
}
</script>
