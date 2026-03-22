<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Browse Placement Drives</h5>

    <div class="row g-2 mb-3">
      <div class="col-md-5">
        <input v-model="search" type="text" class="form-control"
               placeholder="Search by job title or skills..." @input="fetchDrives" />
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="drives.length === 0" class="text-muted text-center py-5">
      No drives available right now.
    </div>
    <div v-else class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="d in drives" :key="d.id">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="fw-bold mb-0">{{ d.job_title }}</h6>
              <span class="badge" :class="d.eligible ? 'bg-success' : 'bg-warning text-dark'">
                {{ d.eligible ? 'Eligible' : 'Not eligible' }}
              </span>
            </div>
            <p class="text-primary small fw-medium mb-2">{{ d.company_name }}</p>
            <p class="text-muted small mb-2 text-truncate">{{ d.job_description || 'No description provided.' }}</p>
            <div class="row g-1 small text-muted">
              <div class="col-6">💰 ₹{{ d.salary_min }}–{{ d.salary_max }} LPA</div>
              <div class="col-6">📍 {{ d.location || 'Remote' }}</div>
              <div class="col-6">🎓 Min CGPA: {{ d.min_cgpa }}</div>
              <div class="col-6">📅 {{ formatDate(d.application_deadline) }}</div>
            </div>
            <div v-if="!d.eligible" class="alert alert-warning py-1 px-2 small mt-2 mb-0">
              {{ d.eligibility_note }}
            </div>
          </div>
          <div class="card-footer bg-transparent">
            <button v-if="d.already_applied"
                    class="btn btn-sm btn-secondary w-100" disabled>Applied ✓</button>
            <button v-else-if="d.eligible"
                    class="btn btn-sm btn-primary w-100"
                    :disabled="applying === d.id"
                    @click="apply(d.id)">
              <span v-if="applying === d.id" class="spinner-border spinner-border-sm me-1"></span>
              Apply Now
            </button>
            <button v-else class="btn btn-sm btn-outline-secondary w-100" disabled>
              Not Eligible
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentDrivesView',
  data() { return { drives: [], loading: true, search: '', applying: null } },
  created() { this.fetchDrives() },
  methods: {
    async fetchDrives() {
      this.loading = true
      try {
        const { data } = await api.get('/student/drives', { params: { q: this.search } })
        this.drives = data
      } finally { this.loading = false }
    },
    async apply(driveId) {
      this.applying = driveId
      try {
        await api.post(`/student/drives/${driveId}/apply`)
        const d = this.drives.find(x => x.id === driveId)
        if (d) d.already_applied = true
      } catch (err) {
        alert(err.response?.data?.message || 'Application failed.')
      } finally { this.applying = null }
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN') : '—' },
  },
}
</script>
