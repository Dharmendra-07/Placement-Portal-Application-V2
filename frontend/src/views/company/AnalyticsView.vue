<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Recruitment Analytics</h5>
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else class="row g-4">

      <!-- Per-drive funnel grouped bar -->
      <div class="col-12">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white fw-semibold">
            Application Funnel per Drive
          </div>
          <div class="card-body">
            <canvas ref="funnelChart" height="80"></canvas>
          </div>
        </div>
      </div>

      <!-- Status doughnut -->
      <div class="col-md-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Application Status
          </div>
          <div class="card-body d-flex align-items-center justify-content-center">
            <canvas ref="statusChart" height="220" style="max-height:260px"></canvas>
          </div>
        </div>
      </div>

      <!-- CGPA distribution bar -->
      <div class="col-md-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Applicant CGPA Distribution
          </div>
          <div class="card-body">
            <canvas ref="cgpaChart" height="180"></canvas>
          </div>
        </div>
      </div>

      <!-- Department pie -->
      <div class="col-md-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Applicants by Department
          </div>
          <div class="card-body d-flex align-items-center justify-content-center">
            <canvas ref="deptChart" height="220" style="max-height:260px"></canvas>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import api from '../../api'
import { buildGroupedBar, buildDoughnut, buildBar } from '../../utils/chartHelpers'

export default {
  name: 'CompanyAnalyticsView',
  data() { return { loading: true, data: {}, charts: [] } },
  async mounted() {
    try {
      const { data } = await api.get('/analytics/company')
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
        buildGroupedBar(this.$refs.funnelChart,
          d.funnel?.labels || [],
          [{ label: 'Applied',     data: d.funnel?.applied     || [], color: '#0d6efd' },
           { label: 'Shortlisted', data: d.funnel?.shortlisted || [], color: '#fd7e14' },
           { label: 'Selected',    data: d.funnel?.selected    || [], color: '#198754' }]),
        buildDoughnut(this.$refs.statusChart,
          Object.keys(d.status_breakdown  || {}),
          Object.values(d.status_breakdown || {})),
        buildBar(this.$refs.cgpaChart,
          d.cgpa_distribution?.labels || [],
          d.cgpa_distribution?.data   || [],
          'Applicants', '#6f42c1'),
        buildDoughnut(this.$refs.deptChart,
          d.department_breakdown?.labels || [],
          d.department_breakdown?.data   || []),
      ].filter(Boolean)
    },
  },
}
</script>
