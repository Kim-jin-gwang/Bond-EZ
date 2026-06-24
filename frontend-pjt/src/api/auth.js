import { apiGet, apiPost, apiDelete } from './client'

/**
 * 로그인 요청
 * @param {Object} credentials - { username: '...', password: '...' }
 */
export function loginApi(credentials) {
  return apiPost('/auth/login', credentials)
}

/**
 * 회원가입 요청
 * @param {Object} userData - { username, email, password, password_confirm, first_name, last_name }
 */
export function signupApi(userData) {
  return apiPost('/auth/signup', userData)
}

/**
 * 로그아웃 요청
 */
export function logoutApi() {
  return apiPost('/auth/logout')
}

/**
 * 현재 로그인한 사용자 정보 조회
 */
export function fetchMeApi() {
  return apiGet('/auth/me')
}

/**
 * 사용자 정보 수정 요청
 * @param {Object} updateData - { email, first_name, last_name }
 */
export function updateMeApi(updateData) {
  return apiPost('/auth/me', updateData, { method: 'PATCH' })
}

/**
 * 회원탈퇴 요청
 */
export function withdrawApi() {
  return apiDelete('/auth/me')
}

