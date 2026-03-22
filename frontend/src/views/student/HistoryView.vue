<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Application History</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="applications.length === 0" class="text-muted text-center py-5">
      No applications yet.
    </div>
    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th>#</th>
              <th>Company</th>
              <th>Job Title</th>
              <th>Applied On</th>
              <th>Interview</th>
              <th>Status</th>
              <th>Remarks</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in applications" :key="a.id">
              <td class="text-muted small">{{ a.id }}</td>
              <td class="small fw-medium">{{ a.company_name }}</td>
              <td class="small">{{ a.job_title }}</td>
              <td class="small">{{ formatDate(a.applied_at) }}</td>
              <td class="small">
                {{ a.interview_type || '—' }}
                <div v-if="a.interview_date" class="text-muted" style="font-size:11px">
                  {{ formatDate(a.interview_date) }}
                </div>
              </td>
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
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentHistoryView',
  data() { return { applications: [], loading: true } },
  async created() {
    try {
      const { data } = await api.get('/student/applications')
      this.applications = data
    } finally { this.loading = false }
  },
  methods: {
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
