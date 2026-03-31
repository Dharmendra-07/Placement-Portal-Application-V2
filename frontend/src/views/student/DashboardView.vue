<template>
  <div class="container-fluid py-4 px-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Header -->
      <div class="d-flex align-items-start justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <h5 class="fw-bold mb-0">Welcome, {{ data.student?.full_name }}</h5>
          <span class="text-muted small">
            {{ data.student?.department }} · Year {{ data.student?.year }} ·
            CGPA {{ data.student?.cgpa }}
          </span>
        </div>
        <router-link to="/student/profile" class="btn btn-sm btn-outline-primary">
          Edit Profile
        </router-link>
      </div>

      <!-- Stat cards -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-4 col-lg-2" v-for="s in statCards" :key="s.label">
          <div class="card border-0 shadow-sm text-center h-100">
            <div class="card-body py-3">
              <div class="fs-2 fw-bold" :class="s.color">{{ s.value }}</div>
              <div class="text-muted small mt-1">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Upcoming interviews alert -->
      <div v-if="data.upcoming_interviews?.length" class="alert alert-info border-0 mb-4">
        <div class="fw-medium mb-2">Upcoming Interviews ({{ data.upcoming_interviews.length }})</div>
        <div v-for="i in data.upcoming_interviews" :key="i.id"
             class="d-flex justify-content-between align-items-center py-1
                    border-bottom border-info border-opacity-25">
          <div>
            <span class="fw-medium small">{{ i.company_name }}</span>
            <span class="text-muted small ms-2">{{ i.job_title }}</span>
          </div>
          <div class="text-end small">
            <span class="badge bg-info text-dark me-1">{{ i.interview_type }}</span>
            {{ formatDate(i.interview_date) }}
          </div>
        </div>
      </div>

      <div class="row g-4">
        <!-- Available drives -->
        <div class="col-lg-7">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold
                        d-flex justify-content-between align-items-center">
              Available Drives
              <router-link to="/student/drives"
                           class="btn btn-sm btn-outline-primary">Browse all</router-link>
            </div>
            <div class="card-body p-0">
              <div v-if="!eligibleDrives.length"
                   class="text-muted text-center py-4 small">
                No eligible drives available right now.
              </div>
              <div v-else class="list-group list-group-flush">
                <div v-for="d in eligibleDrives.slice(0, 5)" :key="d.id"
                     class="list-group-item py-3">
                  <div class="d-flex justify-content-between align-items-start">
                    <div class="me-2">
                      <div class="fw-medium">{{ d.job_title }}</div>
                      <div class="text-muted small">
                        {{ d.company_name }} ·
                        {{ d.salary_min ? `₹${d.salary_min}–${d.salary_max} LPA` : 'Salary not disclosed' }} ·
                        Deadline: {{ formatDate(d.application_deadline) }}
                      </div>
                    </div>
                    <div class="d-flex gap-1 flex-shrink-0">
                      <button v-if="!d.already_applied"
                              class="btn btn-sm btn-primary"
                              :disabled="applying === d.id"
                              @click="applyNow(d.id)">
                        <span v-if="applying === d.id"
                              class="spinner-border spinner-border-sm me-1"></span>
                        Apply
                      </button>
                      <span v-else class="badge bg-secondary align-self-center">
                        Applied
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent applications -->
        <div class="col-lg-5">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold
                        d-flex justify-content-between align-items-center">
              My Applications
              <router-link to="/student/applications"
                           class="btn btn-sm btn-outline-secondary">View all</router-link>
            </div>
            <div class="card-body p-0">
              <div v-if="!data.applications?.length"
                   class="text-muted text-center py-4 small">
                You haven't applied to any drives yet.
              </div>
              <ul v-else class="list-group list-group-flush">
                <li v-for="a in data.applications?.slice(0, 6)" :key="a.id"
                    class="list-group-item py-2">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <div class="fw-medium small">{{ a.company_name }}</div>
                      <div class="text-muted" style="font-size:11px">
                        {{ a.job_title }} · {{ formatDate(a.applied_at) }}
                      </div>
                    </div>
                    <span class="badge" :class="appBadge(a.status)">
                      {{ a.status }}
                    </span>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Placement confirmation -->
      <div v-if="data.placements?.length" class="card border-0 shadow-sm mt-4">
        <div class="card-header bg-white fw-semibold text-success">
          Placement Confirmations
        </div>
        <div class="card-body p-0">
          <ul class="list-group list-group-flush">
            <li v-for="p in data.placements" :key="p.id"
                class="list-group-item py-3">
              <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div>
                  <div class="fw-medium">{{ p.company_name }}</div>
                  <div class="text-muted small">
                    {{ p.position }} ·
                    {{ p.salary ? `₹${p.salary} LPA` : '' }} ·
                    Joining: {{ p.joining_date || 'TBD' }}
                  </div>
                </div>
                <a v-if="p.offer_letter_url"
                   :href="p.offer_letter_url"
                   target="_blank"
                   class="btn btn-sm btn-outline-success">
                  Download Offer Letter
                </a>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentDashboard',
  data() { return { loading: true, data: {}, applying: null } },
  computed: {
    statCards() {
      const s = this.data.stats || {}
      return [
        { label: 'Available drives', value: s.total_drives   || 0, color: 'text-primary'   },
        { label: 'Applied',          value: s.total_applied  || 0, color: 'text-secondary' },
        { label: 'Shortlisted',      value: s.shortlisted    || 0, color: 'text-info'      },
        { label: 'Waiting',          value: s.waiting        || 0, color: 'text-warning'   },
        { label: 'Selected',         value: s.selected       || 0, color: 'text-success'   },
        { label: 'Rejected',         value: s.rejected       || 0, color: 'text-danger'    },
      ]
    },
    eligibleDrives() {
      return (this.data.drives || []).filter(d => d.eligible)
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
      this.applying = driveId
      try {
        await api.post(`/student/drives/${driveId}/apply`)
        const d = this.data.drives?.find(x => x.id === driveId)
        if (d) d.already_applied = true
        if (this.data.stats) this.data.stats.total_applied++
      } catch (err) {
        alert(err.response?.data?.message || 'Application failed.')
      } finally { this.applying = null }
    },
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        selected: 'bg-success',  rejected: 'bg-danger',
        waiting:  'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString('en-IN') : '—'
    },
  },
}
</script>
