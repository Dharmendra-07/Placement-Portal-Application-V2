<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Manage Companies</h5>

    <!-- Filters -->
    <div class="row g-2 mb-3 align-items-end">
      <div class="col-md-4">
        <label class="form-label small fw-medium">Search</label>
        <input v-model="filters.q" type="text" class="form-control"
               placeholder="Name, location, HR contact..." @input="fetchCompanies" />
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-medium">Industry</label>
        <input v-model="filters.industry" type="text" class="form-control"
               placeholder="IT, Finance..." @input="fetchCompanies" />
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-medium">Status</label>
        <select v-model="filters.status" class="form-select" @change="fetchCompanies">
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
      <div class="col-md-2">
        <button class="btn btn-outline-secondary w-100" @click="resetFilters">Reset</button>
      </div>
      <div class="col-md-2 text-end">
        <span class="text-muted small">{{ pagination.total }} total</span>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="companies.length === 0" class="text-muted text-center py-5">
      No companies found.
    </div>

    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th>#</th>
              <th>Company</th>
              <th>Industry</th>
              <th>HR Contact</th>
              <th>Email</th>
              <th>Status</th>
              <th>Blacklisted</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in companies" :key="c.id">
              <td class="text-muted small">{{ c.id }}</td>
              <td>
                <div class="fw-medium">{{ c.name }}</div>
                <div class="text-muted small">{{ c.location || '—' }}</div>
              </td>
              <td class="small">{{ c.industry || '—' }}</td>
              <td class="small">
                <div>{{ c.hr_contact_name || '—' }}</div>
                <div class="text-muted">{{ c.hr_contact_phone || '' }}</div>
              </td>
              <td class="small">{{ c.email }}</td>
              <td>
                <span class="badge" :class="statusBadge(c.approval_status)">
                  {{ c.approval_status }}
                </span>
              </td>
              <td>
                <span v-if="c.is_blacklisted" class="badge bg-dark">Blacklisted</span>
                <span v-else class="text-muted small">—</span>
              </td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <button v-if="c.approval_status === 'pending'"
                          class="btn btn-sm btn-success" @click="approve(c.id)">Approve</button>
                  <button v-if="c.approval_status === 'pending'"
                          class="btn btn-sm btn-danger" @click="reject(c.id)">Reject</button>
                  <button v-if="!c.is_blacklisted"
                          class="btn btn-sm btn-outline-danger"
                          @click="blacklist(c.id)">Blacklist</button>
                  <button v-else
                          class="btn btn-sm btn-outline-success"
                          @click="unblacklist(c.id)">Restore</button>
                  <button class="btn btn-sm btn-outline-secondary"
                          @click="remove(c.id)">Remove</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
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
  name: 'AdminCompaniesView',
  data() {
    return {
      companies: [],
      loading: true,
      filters: { q: '', industry: '', status: '' },
      pagination: { page: 1, pages: 1, total: 0 },
    }
  },
  created() { this.fetchCompanies() },
  methods: {
    async fetchCompanies(page = 1) {
      this.loading = true
      try {
        const { data } = await api.get('/admin/companies', {
          params: { ...this.filters, page }
        })
        this.companies  = data.companies
        this.pagination = { page: data.page, pages: data.pages, total: data.total }
      } finally { this.loading = false }
    },
    changePage(p) { if (p >= 1 && p <= this.pagination.pages) this.fetchCompanies(p) },
    resetFilters() { this.filters = { q: '', industry: '', status: '' }; this.fetchCompanies() },
    async approve(id)     { await api.put(`/admin/companies/${id}/approve`);      this.fetchCompanies() },
    async reject(id)      { await api.put(`/admin/companies/${id}/reject`);       this.fetchCompanies() },
    async blacklist(id)   {
      if (!confirm('Blacklist this company and close all their drives?')) return
      await api.put(`/admin/companies/${id}/blacklist`);  this.fetchCompanies()
    },
    async unblacklist(id) { await api.put(`/admin/companies/${id}/unblacklist`);  this.fetchCompanies() },
    async remove(id) {
      if (!confirm('Permanently delete this company? This cannot be undone.')) return
      await api.delete(`/admin/companies/${id}`); this.fetchCompanies()
    },
    statusBadge(s) {
      return { pending: 'bg-warning text-dark', approved: 'bg-success', rejected: 'bg-danger' }[s] || 'bg-secondary'
    },
  },
}
</script>
