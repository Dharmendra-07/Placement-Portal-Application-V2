<template>
  <div class="container-fluid py-4 px-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else>
      <div class="d-flex align-items-center gap-3 mb-4">
        <div>
          <h5 class="fw-bold mb-0">Welcome, {{ data.student?.full_name }}</h5>
          <span class="text-muted small">
            {{ data.student?.department }} · Year {{ data.student?.year }} · CGPA {{ data.student?.cgpa }}
          </span>
        </div>
        <router-link to="/student/profile" class="btn btn-sm btn-outline-primary ms-auto">
          Edit Profile
        </router-link>
      </div>

      <!-- Stats -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3" v-for="s in stats" :key="s.label">
          <div class="card border-0 shadow-sm text-center h-100">
            <div class="card-body py-3">
              <div class="fs-3 fw-bold" :class="s.color">{{ s.value }}</div>
              <div class="text-muted small">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Drives available -->
      <div class="card border-0 shadow-sm mb-3">
        <div class="card-header bg-white fw-semibold d-flex justify-content-between">
          Available Drives
          <router-link to="/student/drives" class="btn btn-sm btn-outline-primary">View All</router-link>
        </div>
        <div class="card-body p-0">
          <div v-if="data.drives?.length === 0" class="text-muted text-center py-4 small">
            No approved drives available right now.
          </div>
          <table v-else class="table table-hover mb-0 align-middle">
            <thead class="table-light">
              <tr><th>Drive</th><th>Company</th><th>Salary</th><th>Deadline</th><th>Eligible</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="d in data.drives?.slice(0, 5)" :key="d.id">
                <td>
                  <div class="fw-medium">{{ d.job_title }}</div>
                  <div class="text-muted small">{{ d.job_type }}</div>
                </td>
                <td class="small">{{ d.company_name }}</td>
                <td class="small">₹{{ d.salary_min }}–{{ d.salary_max }} LPA</td>
                <td class="small">{{ formatDate(d.application_deadline) }}</td>
                <td>
                  <span class="badge" :class="d.eligible ? 'bg-success' : 'bg-warning text-dark'">
                    {{ d.eligible ? 'Eligible' : 'Not eligible' }}
                  </span>
                </td>
                <td>
                  <button v-if="!d.already_applied && d.eligible"
                          class="btn btn-sm btn-primary"
                          @click="applyNow(d.id)">Apply</button>
                  <span v-else-if="d.already_applied" class="badge bg-secondary">Applied</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent applications -->
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white fw-semibold d-flex justify-content-between">
          My Applications
          <router-link to="/student/history" class="btn btn-sm btn-outline-secondary">View All</router-link>
        </div>
        <div class="card-body p-0">
          <div v-if="data.applications?.length === 0" class="text-muted text-center py-4 small">
            You haven't applied to any drives yet.
          </div>
          <table v-else class="table mb-0 align-middle">
            <thead class="table-light">
              <tr><th>Company</th><th>Job</th><th>Date</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="a in data.applications?.slice(0, 5)" :key="a.id">
                <td class="small">{{ a.company_name }}</td>
                <td class="small fw-medium">{{ a.job_title }}</td>
                <td class="small">{{ formatDate(a.applied_at) }}</td>
                <td>
                  <span class="badge" :class="appBadge(a.status)">{{ a.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentDashboard',
  data() { return { loading: true, data: {} } },
  computed: {
    stats() {
      const apps = this.data.applications || []
      return [
        { label: 'Available Drives', value: this.data.drives?.length || 0, color: 'text-primary' },
        { label: 'Applications',     value: apps.length, color: 'text-info' },
        { label: 'Shortlisted',      value: apps.filter(a => a.status === 'shortlisted').length, color: 'text-warning' },
        { label: 'Selected',         value: (this.data.placements || []).length, color: 'text-success' },
      ]
    },
  },
  async created() {
    try {
      const { data } = await api.get('/student/dashboard')
      this.data = data
    } finally { this.loading = false }
  },
  methods: {
    async applyNow(driveId) {
      try {
        await api.post(`/student/drives/${driveId}/apply`)
        const { data } = await api.get('/student/dashboard')
        this.data = data
      } catch (err) {
        alert(err.response?.data?.message || 'Application failed.')
      }
    },
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        selected: 'bg-success', rejected: 'bg-danger', waiting: 'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN') : '—' },
  },
}
</script>
