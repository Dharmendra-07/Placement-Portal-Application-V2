import { createStore } from 'vuex'
import api from '../api'

export default createStore({
  state: {
    token:   localStorage.getItem('access_token') || null,
    user:    JSON.parse(localStorage.getItem('user') || 'null'),
    profile: JSON.parse(localStorage.getItem('profile') || 'null'),
  },

  getters: {
    isAuthenticated: (state) => !!state.token,
    role:            (state) => state.user?.role || null,
    isAdmin:         (state) => state.user?.role === 'admin',
    isCompany:       (state) => state.user?.role === 'company',
    isStudent:       (state) => state.user?.role === 'student',
    currentUser:     (state) => state.user,
    profile:         (state) => state.profile,
  },

  mutations: {
    SET_AUTH(state, { token, user, profile }) {
      state.token   = token
      state.user    = user
      state.profile = profile
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('profile', JSON.stringify(profile))
    },
    CLEAR_AUTH(state) {
      state.token   = null
      state.user    = null
      state.profile = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('profile')
    },
    SET_PROFILE(state, profile) {
      state.profile = profile
      localStorage.setItem('profile', JSON.stringify(profile))
    },
  },

  actions: {
    async login({ commit }, { email, password }) {
      const { data } = await api.post('/auth/login', { email, password })
      commit('SET_AUTH', {
        token:   data.access_token,
        user:    { id: data.user_id, role: data.role, email },
        profile: data.profile,
      })
      return data.role
    },

    async registerStudent({ commit }, payload) {
      const { data } = await api.post('/auth/register/student', payload)
      commit('SET_AUTH', {
        token:   data.access_token,
        user:    { id: data.user_id, role: data.role, email: payload.email },
        profile: data.profile,
      })
      return data
    },

    async registerCompany(_, payload) {
      const { data } = await api.post('/auth/register/company', payload)
      return data   // no token — pending approval
    },

    async fetchMe({ commit }) {
      const { data } = await api.get('/auth/me')
      commit('SET_PROFILE', data.profile)
      return data
    },

    logout({ commit }) {
      commit('CLEAR_AUTH')
    },
  },
})
