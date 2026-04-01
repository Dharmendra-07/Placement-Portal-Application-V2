<template>
  <div>
    <!-- Hero -->
    <section style="background:linear-gradient(135deg,#0d6efd 0%,#0a3d8f 100%);
                    padding:60px 20px 80px;color:#fff;text-align:center">
      <div class="container" style="max-width:700px">
        <div class="mb-3" style="font-size:3rem">🎓</div>
        <h1 class="fw-bold mb-2" style="font-size:2.2rem">Campus Placement Portal</h1>
        <p class="mb-4 opacity-75">
          Connecting students with their dream companies — all in one place.
        </p>
        <div class="d-flex gap-3 justify-content-center flex-wrap">
          <router-link to="/login"
                       class="btn btn-light fw-semibold px-4">
            Sign In
          </router-link>
          <router-link to="/register/student"
                       class="btn btn-outline-light px-4">
            Register as Student
          </router-link>
        </div>
      </div>
    </section>

    <!-- Highlight stats -->
    <section class="py-4" style="background:#f8f9fc">
      <div class="container">
        <div class="row g-3 justify-content-center" v-if="stats">
          <div class="col-6 col-md-3" v-for="h in highlights" :key="h.label">
            <div class="card border-0 shadow-sm text-center stat-card h-100">
              <div class="card-body py-3">
                <div class="fs-2 fw-bold text-primary">{{ h.value }}</div>
                <div class="text-muted small">{{ h.label }}</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-3">
          <div class="spinner-border text-primary"></div>
        </div>
      </div>
    </section>

    <!-- Charts section -->
    <section class="py-5">
      <div class="container">
        <h4 class="fw-bold text-center mb-4">Placement Trends</h4>

        <div class="row g-4" v-if="stats">
          <!-- Monthly drives + placements (line) -->
          <div class="col-lg-8">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white fw-semibold">
                Monthly Activity (last 6 months)
              </div>
              <div class="card-body">
                <canvas ref="trendChart" height="100"></canvas>
              </div>
            </div>
          </div>

          <!-- Application funnel (doughnut) -->
          <div class="col-lg-4">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white fw-semibold">
                Application Funnel
              </div>
              <div class="card-body d-flex align-items-center
                           justify-content-center">
                <canvas ref="funnelChart" height="200"
                        style="max-height:240px"></canvas>
              </div>
            </div>
          </div>

          <!-- Top skills (horizontal bar) -->
          <div class="col-12">
            <div class="card border-0 shadow-sm">
              <div class="card-header bg-white fw-semibold">
                Top Skills in Demand
              </div>
              <div class="card-body">
                <canvas ref="skillChart" height="60"></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-5 text-center"
             style="background:#0d6efd;color:#fff">
      <h4 class="fw-bold mb-3">Ready to find your dream job?</h4>
      <router-link to="/register/student"
                   class="btn btn-light fw-semibold px-5">
        Get Started
      </router-link>
    </section>
  </div>
</template>

<script>
import api from '../api'
import {
  Chart, LineController, BarController, DoughnutController,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Tooltip, Legend, Filler,
} from 'chart.js'

Chart.register(
  LineController, BarController, DoughnutController,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Tooltip, Legend, Filler,
)

export default {
  name: 'LandingView',
  data() { return { stats: null, charts: [] } },
  computed: {
    highlights() {
      const h = this.stats?.highlights || {}
      return [
        { label: 'Companies',      value: h.total_companies  || 0 },
        { label: 'Students',       value: h.total_students   || 0 },
        { label: 'Students Placed',value: h.total_placed     || 0 },
        { label: 'Placement Rate', value: `${h.placement_rate || 0}%` },
      ]
    },
  },
  async mounted() {
    const { data } = await api.get('/analytics/public')
    this.stats = data
    this.$nextTick(() => this.buildCharts())
  },
  beforeUnmount() {
    this.charts.forEach(c => c.destroy())
  },
  methods: {
    buildCharts() {
      const d = this.stats
      const COLORS = ['#0d6efd','#198754','#fd7e14','#dc3545','#6f42c1','#0dcaf0']

      // Trend line chart
      this.charts.push(new Chart(this.$refs.trendChart, {
        type: 'line',
        data: {
          labels: d.labels,
          datasets: [
            {
              label: 'Drives',
              data: d.monthly_drives,
              borderColor: '#0d6efd',
              backgroundColor: 'rgba(13,110,253,.08)',
              tension: 0.4, fill: true,
            },
            {
              label: 'Placed',
              data: d.monthly_placements,
              borderColor: '#198754',
              backgroundColor: 'rgba(25,135,84,.08)',
              tension: 0.4, fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'top' } },
          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        },
      }))

      // Funnel doughnut
      const f = d.funnel
      this.charts.push(new Chart(this.$refs.funnelChart, {
        type: 'doughnut',
        data: {
          labels: ['Drives', 'Applied', 'Shortlisted', 'Placed'],
          datasets: [{
            data: [f.drives, f.applications, f.shortlisted, f.placed],
            backgroundColor: ['#0d6efd','#fd7e14','#ffc107','#198754'],
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom' } },
          cutout: '65%',
        },
      }))

      // Skills bar
      const skills = d.top_skills || []
      this.charts.push(new Chart(this.$refs.skillChart, {
        type: 'bar',
        data: {
          labels: skills.map(s => s.skill),
          datasets: [{
            label: 'Drives requiring this skill',
            data: skills.map(s => s.count),
            backgroundColor: COLORS.slice(0, skills.length)
              .concat(Array(skills.length).fill('#6c757d'))
              .slice(0, skills.length),
            borderRadius: 6,
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        },
      }))
    },
  },
}
</script>
