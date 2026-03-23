<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Interview Schedule</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="interviews.length === 0"
         class="text-muted text-center py-5">
      No interviews scheduled yet.
    </div>

    <div v-else>
      <!-- Upcoming -->
      <div v-if="upcoming.length" class="mb-4">
        <h6 class="fw-semibold text-success mb-3">Upcoming</h6>
        <div class="row g-3">
          <div class="col-md-6" v-for="a in upcoming" :key="a.id">
            <div class="card border-0 shadow-sm border-start border-4 border-success">
              <div class="card-body">
                <div class="d-flex justify-content-between mb-2">
                  <h6 class="fw-bold mb-0">{{ a.company_name }}</h6>
                  <span class="badge bg-info text-dark">{{ a.interview_type }}</span>
                </div>
                <p class="text-muted small mb-2">{{ a.job_title }}</p>
                <div class="d-flex align-items-center gap-2">
                  <span class="badge bg-success">
                    {{ formatDateTime(a.interview_date) }}
                  </span>
                </div>
                <div v-if="a.remarks"
                     class="text-muted small mt-2 border-start border-3
                            border-success ps-2">
                  {{ a.remarks }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Past -->
      <div v-if="past.length">
        <h6 class="fw-semibold text-muted mb-3">Past</h6>
        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead class="table-light">
              <tr>
                <th>Company</th>
                <th>Job Title</th>
                <th>Type</th>
                <th>Date</th>
                <th>Outcome</th>
                <th>Remarks</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in past" :key="a.id">
                <td class="fw-medium small">{{ a.company_name }}</td>
                <td class="small">{{ a.job_title }}</td>
                <td class="small">{{ a.interview_type }}</td>
                <td class="small">{{ formatDateTime(a.interview_date) }}</td>
                <td>
                  <span class="badge" :class="appBadge(a.status)">{{ a.status }}</span>
                </td>
                <td class="small text-muted">{{ a.remarks || '—' }}</td>
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
  name: 'StudentInterviewsView',
  data() { return { interviews: [], loading: true } },
  computed: {
    upcoming() {
      const now = new Date()
      return this.interviews.filter(a => new Date(a.interview_date) >= now)
    },
    past() {
      const now = new Date()
      return this.interviews.filter(a => new Date(a.interview_date) < now)
    },
  },
  async created() {
    try {
      const { data } = await api.get('/student/interviews')
      this.interviews = data
    } finally { this.loading = false }
  },
  methods: {
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        selected: 'bg-success',  rejected: 'bg-danger',
        waiting:  'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
    formatDateTime(d) {
      return d ? new Date(d).toLocaleString('en-IN',
        { dateStyle: 'medium', timeStyle: 'short' }) : '—'
    },
  },
}
</script>
