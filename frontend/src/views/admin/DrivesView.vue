<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Manage Placement Drives</h5>

    <div class="row g-2 mb-3 align-items-end">
      <div class="col-md-4">
        <label class="form-label small fw-medium">Search job title</label>
        <input v-model="filters.q" type="text" class="form-control"
               placeholder="Software Engineer, Data Scientist..." @input="fetchDrives" />
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-medium">Status</label>
        <select v-model="filters.status" class="form-select" @change="fetchDrives">
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="closed">Closed</option>
        </select>
      </div>
      <div class="col-md-2">
        <button class="btn btn-outline-secondary w-100" @click="resetFilters">Reset</button>
      </div>
      <div class="col text-end">
        <span class="text-muted small">{{ pagination.total }} drives</span>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="drives.length === 0" class="text-muted text-center py-5">
      No drives found.
    </div>
    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th>#</th>
              <th>Job Title</th>
              <th>Company</th>
              <th>Eligibility</th>
              <th>Salary (LPA)</th>
              <th>Deadline</th>
              <th>Applicants</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in drives" :key="d.id">
              <td class="text-muted small">{{ d.id }}</td>
              <td>
                <div class="fw-medium">{{ d.job_title }}</div>
                <div class="text-muted small">{{ d.job_type }} · {{ d.location || 'Remote' }}</div>
              </td>
              <td class="small">{{ d.company_name }}</td>
              <td class="small text-muted">
                <div>CGPA ≥ {{ d.min_cgpa }}</div>
                <div>{{ d.eligible_branches || 'All' }}</div>
              </td>
              <td class="small">
                {{ d.salary_min ? `₹${d.salary_min}–${d.salary_max}` : '—' }}
              </td>
              <td class="small">{{ formatDate(d.application_deadline) }}</td>
              <td class="text-center">
                <span class="badge bg-secondary">{{ d.applicant_count }}</span>
              </td>
              <td>
                <span class="badge" :class="statusBadge(d.status)">{{ d.status }}</span>
              </td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <button v-if="d.status === 'pending'"
                          class="btn btn-sm btn-success" @click="approve(d.id)">Approve</button>
                  <button v-if="d.status === 'pending'"
                          class="btn btn-sm btn-danger"  @click="reject(d.id)">Reject</button>
                  <button class="btn btn-sm btn-outline-secondary"
                          @click="remove(d.id)">Remove</button>
                </div>
              </td>
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
  name: 'AdminDrivesView',
  data() {
    return {
      drives: [], loading: true,
      filters: { q: '', status: 'pending' },
      pagination: { page: 1, pages: 1, total: 0 },
    }
  },
  created() { this.fetchDrives() },
  methods: {
    async fetchDrives(page = 1) {
      this.loading = true
      try {
        const { data } = await api.get('/admin/drives', {
          params: { ...this.filters, page }
        })
        this.drives     = data.drives
        this.pagination = { page: data.page, pages: data.pages, total: data.total }
      } finally { this.loading = false }
    },
    changePage(p) { if (p >= 1 && p <= this.pagination.pages) this.fetchDrives(p) },
    resetFilters() { this.filters = { q: '', status: '' }; this.fetchDrives() },
    async approve(id) { await api.put(`/admin/drives/${id}/approve`);  this.fetchDrives() },
    async reject(id)  { await api.put(`/admin/drives/${id}/reject`);   this.fetchDrives() },
    async remove(id)  {
      if (!confirm('Remove this drive? All applications will be deleted.')) return
      await api.delete(`/admin/drives/${id}`); this.fetchDrives()
    },
    statusBadge(s) {
      return { pending: 'bg-warning text-dark', approved: 'bg-success', closed: 'bg-secondary' }[s] || 'bg-secondary'
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN') : '—' },
  },
}
</script>
