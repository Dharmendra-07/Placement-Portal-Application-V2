<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Analytics</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else class="row g-4">

      <!-- Applications vs Placements line -->
      <div class="col-lg-8">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Monthly Applications vs Placements
          </div>
          <div class="card-body">
            <canvas ref="trendChart" height="100"></canvas>
          </div>
        </div>
      </div>

      <!-- Status doughnut -->
      <div class="col-lg-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Application Status Breakdown
          </div>
          <div class="card-body d-flex align-items-center justify-content-center">
            <canvas ref="statusChart" height="220" style="max-height:260px"></canvas>
          </div>
        </div>
      </div>

      <!-- Top companies bar -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Top Companies by Placements
          </div>
          <div class="card-body">
            <canvas ref="companyChart" height="140"></canvas>
          </div>
        </div>
      </div>

      <!-- Skill demand bar -->
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            In-demand Skills
          </div>
          <div class="card-body">
            <canvas ref="skillChart" height="140"></canvas>
          </div>
        </div>
      </div>

      <!-- Department grouped bar -->
      <div class="col-12">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white fw-semibold">
            Department — Applied vs Placed
          </div>
          <div class="card-body">
            <canvas ref="deptChart" height="70"></canvas>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import api from '../../api'
import { buildTrendLine, buildDoughnut, buildBar, buildGroupedBar } from '../../utils/chartHelpers'

export default {
  name: 'AdminAnalyticsView',
  data() { return { loading: true, data: {}, charts: [] } },
  async mounted() {
    try {
      const { data } = await api.get('/analytics/admin')
      this.data = data
      this.loading = false
      this.$nextTick(() => this.buildCharts())
    } catch { this.loading = false }
  },
  beforeUnmount() { this.charts.forEach(c => c.destroy()) },
  methods: {
    buildCharts() {
      const d = this.data
      this.charts = [
        buildTrendLine(this.$refs.trendChart, d.labels,
          [{ label: 'Applications', data: d.monthly_apps,   color: '#0d6efd' },
           { label: 'Placed',       data: d.monthly_placed, color: '#198754' }]),
        buildDoughnut(this.$refs.statusChart,
          Object.keys(d.status_breakdown || {}),
          Object.values(d.status_breakdown || {})),
        buildBar(this.$refs.companyChart,
          d.company_placements?.labels || [],
          d.company_placements?.data   || [],
          'Placements', '#6f42c1'),
        buildBar(this.$refs.skillChart,
          d.skill_demand?.labels || [],
          d.skill_demand?.data   || [],
          'Drives requiring skill', '#0dcaf0'),
        buildGroupedBar(this.$refs.deptChart,
          d.department_stats?.labels  || [],
          [{ label: 'Applied', data: d.department_stats?.applied || [], color: '#0d6efd' },
           { label: 'Placed',  data: d.department_stats?.placed  || [], color: '#198754' }]),
      ].filter(Boolean)
    },
  },
}
</script>
