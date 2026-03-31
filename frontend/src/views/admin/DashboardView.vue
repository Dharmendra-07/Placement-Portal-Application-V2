<template>
  <div class="container-fluid py-4 px-4">
    <div class="d-flex align-items-center justify-content-between mb-4">
      <h5 class="fw-bold mb-0">Admin Dashboard</h5>
      <!-- Global search bar -->
      <div class="input-group" style="max-width:340px">
        <input v-model="searchQ" type="text" class="form-control"
               placeholder="Search students, companies, drives..."
               @keyup.enter="runSearch" />
        <button class="btn btn-outline-secondary" @click="runSearch">Search</button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Stats grid -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3" v-for="s in statCards" :key="s.label">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-body text-center py-3">
              <div class="fs-2 fw-bold" :class="s.color">{{ s.value }}</div>
              <div class="text-muted small mt-1">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Application status pills -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white fw-semibold">Application Status Breakdown</div>
        <div class="card-body d-flex flex-wrap gap-2">
          <span v-for="(count, status) in data.application_status_counts" :key="status"
                class="badge fs-6 fw-normal px-3 py-2" :class="appBadge(status)">
            {{ status }}: {{ count }}
          </span>
        </div>
      </div>

      <div class="row g-4">
        <!-- Pending company approvals -->
        <div class="col-md-6">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold d-flex justify-content-between align-items-center">
              Pending Company Approvals
              <span class="badge bg-warning text-dark">{{ data.pending_companies }}</span>
            </div>
            <div class="card-body p-0">
              <div v-if="!data.pending_company_list?.length"
                   class="text-muted text-center py-4 small">
                All caught up!
              </div>
              <ul v-else class="list-group list-group-flush">
                <li v-for="c in data.pending_company_list" :key="c.id"
                    class="list-group-item d-flex justify-content-between align-items-center py-2">
                  <div>
                    <div class="fw-medium small">{{ c.name }}</div>
                    <div class="text-muted" style="font-size:12px">{{ c.industry }} · {{ c.email }}</div>
                  </div>
                  <div class="d-flex gap-1">
                    <button class="btn btn-sm btn-success" @click="approveCompany(c.id)">✓</button>
                    <button class="btn btn-sm btn-danger"  @click="rejectCompany(c.id)">✗</button>
                  </div>
                </li>
              </ul>
              <div class="card-footer bg-transparent text-end">
                <router-link to="/admin/companies" class="btn btn-sm btn-outline-primary">
                  View all companies →
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent applications -->
        <div class="col-md-6">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold d-flex justify-content-between align-items-center">
              Recent Applications
              <router-link to="/admin/applications" class="btn btn-sm btn-outline-secondary">
                View all
              </router-link>
            </div>
            <div class="card-body p-0">
              <div v-if="!data.recent_applications?.length"
                   class="text-muted text-center py-4 small">No applications yet.</div>
              <ul v-else class="list-group list-group-flush">
                <li v-for="a in data.recent_applications" :key="a.id"
                    class="list-group-item py-2">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <div class="fw-medium small">{{ a.student_name }}</div>
                      <div class="text-muted" style="font-size:12px">
                        {{ a.company_name }} · {{ a.job_title }}
                      </div>
                    </div>
                    <span class="badge" :class="appBadge(a.status)">{{ a.status }}</span>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Global search results -->
      <div v-if="searchResults" class="card border-0 shadow-sm mt-4">
        <div class="card-header bg-white fw-semibold d-flex justify-content-between">
          Search results for "{{ searchQ }}"
          <button class="btn-close" @click="searchResults = null"></button>
        </div>
        <div class="card-body">
          <div v-if="!searchResults.students.length && !searchResults.companies.length && !searchResults.drives.length"
               class="text-muted text-center py-3">No results found.</div>

          <div v-if="searchResults.companies.length">
            <p class="fw-medium small text-uppercase text-muted mb-2">Companies</p>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <span v-for="c in searchResults.companies" :key="c.id"
                    class="badge bg-primary-subtle text-primary px-3 py-2 fw-normal">
                {{ c.name }} ({{ c.approval_status }})
              </span>
            </div>
          </div>

          <div v-if="searchResults.students.length">
            <p class="fw-medium small text-uppercase text-muted mb-2">Students</p>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <span v-for="s in searchResults.students" :key="s.id"
                    class="badge bg-success-subtle text-success px-3 py-2 fw-normal">
                {{ s.full_name }} ({{ s.roll_number || s.email }})
              </span>
            </div>
          </div>

          <div v-if="searchResults.drives.length">
            <p class="fw-medium small text-uppercase text-muted mb-2">Drives</p>
            <div class="d-flex flex-wrap gap-2">
              <span v-for="d in searchResults.drives" :key="d.id"
                    class="badge bg-warning-subtle text-warning-emphasis px-3 py-2 fw-normal">
                {{ d.job_title }} — {{ d.company_name }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'AdminDashboard',
  data() {
    return { loading: true, data: {}, searchQ: '', searchResults: null }
  },
  computed: {
    statCards() {
      return [
        { label: 'Students',          value: this.data.total_students        || 0, color: 'text-primary'   },
        { label: 'Approved Companies',value: this.data.total_companies       || 0, color: 'text-success'   },
        { label: 'Total Drives',      value: this.data.total_drives          || 0, color: 'text-info'      },
        { label: 'Applications',      value: this.data.total_applications    || 0, color: 'text-secondary' },
        { label: 'Selected Students', value: this.data.total_selected        || 0, color: 'text-warning'   },
        { label: 'Pending Companies', value: this.data.pending_companies     || 0, color: 'text-danger'    },
        { label: 'Pending Drives',    value: this.data.pending_drives        || 0, color: 'text-danger'    },
        { label: 'Blacklisted',
          value: (this.data.blacklisted_companies || 0) + (this.data.blacklisted_students || 0),
          color: 'text-dark' },
      ]
    },
  },
  async created() {
    try {
      const { data } = await api.get('/admin/dashboard')
      this.data = data
    } finally { this.loading = false }
  },
  methods: {
    async approveCompany(id) {
      await api.put(`/admin/companies/${id}/approve`)
      const { data } = await api.get('/admin/dashboard')
      this.data = data
    },
    async rejectCompany(id) {
      await api.put(`/admin/companies/${id}/reject`)
      const { data } = await api.get('/admin/dashboard')
      this.data = data
    },
    async runSearch() {
      if (!this.searchQ.trim()) return
      const { data } = await api.get('/admin/search', { params: { q: this.searchQ } })
      this.searchResults = data
    },
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        selected: 'bg-success', rejected: 'bg-danger', waiting: 'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
  },
}
</script>
