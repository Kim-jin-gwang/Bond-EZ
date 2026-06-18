import { indicators } from '../data/indicators'
import { cachedQuery } from './cache'

export function getIndicators() {
  return indicators
}

export function fetchIndicators() {
  return cachedQuery('indicators:list', () => indicators)
}
