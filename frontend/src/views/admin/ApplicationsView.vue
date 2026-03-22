<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">All Applications</h5>

    <div class="row g-2 mb-3 align-items-end">
      <div class="col-md-3">
        <label class="form-label small fw-medium">Status</label>
        <select v-model="filters.status" class="form-select" @change="fetchApps">
          <option value="">All statuses</option>
          <option value="applied">Applied</option>
          <option value="shortlisted">Shortlisted</option>
          <option value="waiting">Waiting</option>
          <option value="selected">Selected</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
      <div class="col-md-2">
        <button class="btn btn-outline-secondary w-100" @click="resetFilters">Reset</button>
      </div>
      <div class="col text-end">
        <span class="text-muted small">{{ pagination.total }} applications</span>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="applications.length === 0" class="text-muted text-center py-5">
      No applications found.
    </div>
    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th>#</th>
              <th>Student</th>
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
              <td>
                <div class="fw-medium small">{{ a.student_name }}</div>
                <div class="text-muted" style="font-size:11px">{{ a.student_dept }} · CGPA {{ a.student_cgpa }}</div>
              </td>
              <td class="small">{{ a.company_name }}</td>
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

      <nav v-if="pagination.pages > 1">
        <ul class="pagination pagination-sm justify-content-center">
          <li class="page-item" :class="{ disabled: pagination.page === 1 }">
            <button class="page-link" @click="changePage(pagination.page - 1)">‹</button>
          </li>
          <li v-for="p in pagination.pages" :key="p"
              class="page-item" :class="{ active: p === pagination.page }">
            <button class="page-link" @click="changePage(p)">{{ p }}</button>
          </li>
          <li class="page-item" :class="{ disabled: pagination.page === pagination.pages }">
            <button class="page-link" @click="changePage(pagination.page + 1)">›</button>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'AdminApplicationsView',
  data() {
    return {
      applications: [], loading: true,
      filters: { status: '' },
      pagination: { page: 1, pages: 1, total: 0 },
    }
  },
  created() { this.fetchApps() },
  methods: {
    async fetchApps(page = 1) {
      this.loading = true
      try {
        const { data } = await api.get('/admin/applications', {
          params: { ...this.filters, page }
        })
        this.applications = data.applications
        this.pagination   = { page: data.page, pages: data.pages, total: data.total }
      } finally { this.loading = false }
    },
    changePage(p) { if (p >= 1 && p <= this.pagination.pages) this.fetchApps(p) },
    resetFilters() { this.filters = { status: '' }; this.fetchApps() },
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
