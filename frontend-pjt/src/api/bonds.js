import { bonds, selectedBond } from '../data/bonds'
import { cachedQuery } from './cache'

export function getBonds() {
  return bonds
}

export function fetchBonds() {
  return cachedQuery('bonds:list', () => bonds)
}

export function getSelectedBond() {
  return selectedBond
}
