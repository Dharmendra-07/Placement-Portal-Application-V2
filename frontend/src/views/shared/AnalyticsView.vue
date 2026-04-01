<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Analytics & Reports</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Summary stats -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-lg-3" v-for="s in summaryCards" :key="s.label">
          <div class="card border-0 shadow-sm text-center h-100 stat-card">
            <div class="card-body py-3">
              <div class="fs-2 fw-bold" :class="s.color">{{ s.value }}</div>
              <div class="text-muted small mt-1">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts grid -->
      <div class="row g-4">

        <!-- Monthly trend -->
        <div class="col-lg-8">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">
              {{ isAdmin ? 'Monthly Placements & Applications' : isCompany ? 'Monthly Applications' : 'My Application Activity' }}
            </div>
            <div class="card-body"><canvas ref="trendChart" height="200"></canvas></div>
          </div>
        </div>

        <!-- Application funnel / status breakdown -->
        <div class="col-lg-4">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">
              {{ isAdmin ? 'Application Funnel' : isStudent ? 'My Status Breakdown' : 'Drive Funnel Summary' }}
            </div>
            <div class="card-body"><canvas ref="funnelChart" height="200"></canvas></div>
          </div>
        </div>

        <!-- Skills chart -->
        <div :class="isStudent ? 'col-lg-6' : 'col-lg-6'">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">
              {{ isStudent ? 'Skills Gap Analysis' : 'Top Skills in Demand' }}
            </div>
            <div class="card-body"><canvas ref="skillsChart" height="220"></canvas></div>
          </div>
        </div>

        <!-- Department or company breakdown -->
        <div class="col-lg-6">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">
              {{ isAdmin ? 'Dept-wise Placements' : isCompany ? 'Applicant Departments' : '' }}
            </div>
            <div v-if="isAdmin || isCompany" class="card-body">
              <canvas ref="deptChart" height="220"></canvas>
            </div>
            <!-- Student: placement rate gauge -->
            <div v-else class="card-body d-flex align-items-center justify-content-center">
              <div class="text-center">
                <div class="display-4 fw-bold text-primary">
                  {{ data.placement_rate || 0 }}%
                </div>
                <p class="text-muted">Your placement rate</p>
                <div class="progress" style="height:12px;width:200px">
                  <div class="progress-bar bg-primary"
                       :style="`width:${data.placement_rate || 0}%`"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Admin only: salary stats + top companies -->
        <template v-if="isAdmin">
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white fw-semibold">Top Companies by Placements</div>
              <div class="card-body"><canvas ref="companyChart" height="220"></canvas></div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="card border-0 shadow-sm">
              <div class="card-header bg-white fw-semibold">Salary Statistics</div>
              <div class="card-body">
                <div class="row g-3 text-center">
                  <div class="col-4">
                    <div class="fs-3 fw-bold text-success">
                      ₹{{ data.salary_stats?.avg || 0 }}
                    </div>
                    <div class="text-muted small">Avg LPA</div>
                  </div>
                  <div class="col-4">
                    <div class="fs-3 fw-bold text-primary">
                      ₹{{ data.salary_stats?.max || 0 }}
                    </div>
                    <div class="text-muted small">Highest LPA</div>
                  </div>
                  <div class="col-4">
                    <div class="fs-3 fw-bold text-secondary">
                      ₹{{ data.salary_stats?.min || 0 }}
                    </div>
                    <div class="text-muted small">Lowest LPA</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Student: skills gap table -->
        <div v-if="isStudent && data.skill_gap?.length" class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white fw-semibold">
              Skills Gap Details
            </div>
            <div class="table-responsive">
              <table class="table table-hover mb-0 align-middle">
                <thead class="table-light">
                  <tr>
                    <th>Skill</th>
                    <th>Drives requiring it</th>
                    <th>In your profile?</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="sk in data.skill_gap" :key="sk.skill">
                    <td class="fw-medium text-capitalize">{{ sk.skill }}</td>
                    <td>
                      <div class="d-flex align-items-center gap-2">
                        <div class="progress flex-grow-1" style="height:8px;max-width:120px">
                          <div class="progress-bar"
                               :class="sk.have ? 'bg-success' : 'bg-danger'"
                               :style="`width:${Math.min(sk.in_demand*10,100)}%`"></div>
                        </div>
                        <span class="text-muted small">{{ sk.in_demand }}</span>
                      </div>
                    </td>
                    <td>
                      <span v-if="sk.have" class="badge bg-success">✓ Have it</span>
                      <span v-else class="badge bg-danger">Missing</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'
import { mapGetters } from 'vuex'

export default {
  name: 'AnalyticsView',
  data() { return { data: {}, loading: true, charts: [] } },
  computed: {
    ...mapGetters(['isAdmin', 'isCompany', 'isStudent']),
    summaryCards() {
      if (this.isAdmin) {
        const s = this.data.salary_stats || {}
        const f = this.data.application_funnel || {}
        return [
          { label: 'Total applications', value: Object.values(f).reduce((a,b)=>a+b,0), color: 'text-primary' },
          { label: 'Total placed',       value: f.selected || 0, color: 'text-success' },
          { label: 'Avg salary (LPA)',   value: `₹${s.avg || 0}`, color: 'text-warning' },
          { label: 'Placement rate',     value: `${this.data.placement_rate || 0}%`, color: 'text-info' },
        ]
      }
      if (this.isCompany) {
        const s = this.data.summary || {}
        return [
          { label: 'Total drives',       value: s.total_drives        || 0, color: 'text-primary' },
          { label: 'Total applications', value: s.total_applications  || 0, color: 'text-info'    },
          { label: 'Selected students',  value: s.total_selected      || 0, color: 'text-success' },
          { label: 'Placement rate',     value: s.total_applications
              ? `${Math.round(s.total_selected/s.total_applications*100)}%` : '0%', color: 'text-warning' },
        ]
      }
      // student
      const sb = this.data.status_breakdown || {}
      return [
        { label: 'Applied',     value: this.data.total_applied || 0,      color: 'text-secondary' },
        { label: 'Shortlisted', value: sb.shortlisted || 0,               color: 'text-info'      },
        { label: 'Selected',    value: sb.selected    || 0,               color: 'text-success'   },
        { label: 'Placement %', value: `${this.data.placement_rate || 0}%`, color: 'text-primary'  },
      ]
    },
  },
  async mounted() {
    const endpoint = this.isAdmin ? '/analytics/admin'
                   : this.isCompany ? '/analytics/company'
                   : '/analytics/student'
    try {
      const { data } = await api.get(endpoint)
      this.data = data
      this.$nextTick(() => this.renderCharts())
    } finally { this.loading = false }
  },
  beforeUnmount() { this.charts.forEach(c => c.destroy()) },
  methods: {
    renderCharts() {
      const C = window.Chart
      if (!C) { console.warn('Chart.js not loaded'); return }

      const COLORS = ['#0d6efd','#198754','#fd7e14','#0dcaf0','#6f42c1',
                      '#d63384','#20c997','#ffc107','#dc3545','#6c757d']

      // Trend chart
      const monthly = this.isAdmin ? (this.data.monthly_trend || [])
                    : (this.data.monthly_apps || [])
      if (this.$refs.trendChart && monthly.length) {
        const datasets = this.isAdmin
          ? [
              { label: 'Placements',    data: monthly.map(m=>m.placements),
                borderColor:'#0d6efd', backgroundColor:'rgba(13,110,253,.08)',
                fill:true, tension:.4 },
              { label: 'Applications',  data: monthly.map(m=>m.applications),
                borderColor:'#198754', backgroundColor:'rgba(25,135,84,.08)',
                fill:true, tension:.4 },
            ]
          : [
              { label: 'Applications',
                data: this.isCompany
                  ? monthly.map(m=>m.applications)
                  : monthly.map(m=>m.count),
                borderColor:'#0d6efd', backgroundColor:'rgba(13,110,253,.1)',
                fill:true, tension:.4 },
            ]
        this.charts.push(new C(this.$refs.trendChart, {
          type: 'line',
          data: { labels: monthly.map(m=>m.label), datasets },
          options: { responsive:true, scales:{ y:{ beginAtZero:true } } },
        }))
      }

      // Funnel / status doughnut
      if (this.$refs.funnelChart) {
        let labels, values
        if (this.isStudent) {
          const sb = this.data.status_breakdown || {}
          labels = Object.keys(sb); values = Object.values(sb)
        } else if (this.isAdmin) {
          const f = this.data.application_funnel || {}
          labels = Object.keys(f); values = Object.values(f)
        } else {
          // company: sum across drives
          const fd = this.data.drive_funnel || []
          labels = ['Applied','Shortlisted','Selected','Rejected']
          values = [
            fd.reduce((a,d)=>a+d.applied,0),
            fd.reduce((a,d)=>a+d.shortlisted,0),
            fd.reduce((a,d)=>a+d.selected,0),
            fd.reduce((a,d)=>a+d.rejected,0),
          ]
        }
        this.charts.push(new C(this.$refs.funnelChart, {
          type: 'doughnut',
          data: { labels, datasets:[{ data:values, backgroundColor:COLORS }] },
          options: { responsive:true, plugins:{ legend:{ position:'bottom' } } },
        }))
      }

      // Skills chart
      if (this.$refs.skillsChart) {
        const skills = this.isStudent
          ? (this.data.skill_gap || []).map(s=>({ skill:s.skill, count:s.in_demand, have:s.have }))
          : (this.data.top_skills || [])
        if (skills.length) {
          this.charts.push(new C(this.$refs.skillsChart, {
            type: 'bar',
            data: {
              labels: skills.map(s=>s.skill),
              datasets:[{
                label: 'In demand',
                data:  skills.map(s=>s.count||s.in_demand),
                backgroundColor: this.isStudent
                  ? skills.map(s => s.have ? '#198754' : '#dc3545')
                  : COLORS,
              }],
            },
            options: {
              indexAxis:'y', responsive:true,
              plugins:{ legend:{ display:false } },
              scales:{ x:{ beginAtZero:true } },
            },
          }))
        }
      }

      // Dept chart
      if (this.$refs.deptChart) {
        const dept = this.isAdmin
          ? (this.data.dept_placements || [])
          : (this.data.dept_distribution || [])
        if (dept.length) {
          this.charts.push(new C(this.$refs.deptChart, {
            type: 'pie',
            data: {
              labels: dept.map(d=>d.dept),
              datasets:[{ data: dept.map(d=>d.count), backgroundColor: COLORS }],
            },
            options: { responsive:true, plugins:{ legend:{ position:'right' } } },
          }))
        }
      }

      // Admin: top companies
      if (this.isAdmin && this.$refs.companyChart) {
        const cos = this.data.top_companies || []
        this.charts.push(new C(this.$refs.companyChart, {
          type:'bar',
          data: {
            labels: cos.map(c=>c.company),
            datasets:[{
              label:'Placements',
              data: cos.map(c=>c.count),
              backgroundColor:'#0d6efd',
            }],
          },
          options: { responsive:true, plugins:{ legend:{ display:false } },
                     scales:{ y:{ beginAtZero:true } } },
        }))
      }
    },
  },
}
</script>
