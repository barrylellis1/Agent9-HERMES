import { useEffect } from 'react'

const SITE_NAME = 'Decision Studio'

type PageMeta = {
  title: string
  description: string
  path: string
  image?: string
}

function upsertMeta(selector: string, attributes: Record<string, string>) {
  let element = document.head.querySelector<HTMLMetaElement>(selector)
  if (!element) {
    element = document.createElement('meta')
    document.head.appendChild(element)
  }

  Object.entries(attributes).forEach(([name, value]) => {
    element?.setAttribute(name, value)
  })
}

function upsertCanonical(url: string) {
  let link = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.rel = 'canonical'
    document.head.appendChild(link)
  }

  link.href = url
}

export function usePageMeta({ title, description, path, image }: PageMeta) {
  useEffect(() => {
    const canonicalUrl = `https://decision-studios.com${path}`

    document.title = title
    upsertCanonical(canonicalUrl)
    upsertMeta('meta[name="description"]', { name: 'description', content: description })
    upsertMeta('meta[property="og:title"]', { property: 'og:title', content: title })
    upsertMeta('meta[property="og:description"]', { property: 'og:description', content: description })
    upsertMeta('meta[property="og:type"]', { property: 'og:type', content: 'website' })
    upsertMeta('meta[property="og:url"]', { property: 'og:url', content: canonicalUrl })
    upsertMeta('meta[property="og:site_name"]', { property: 'og:site_name', content: SITE_NAME })
    upsertMeta('meta[name="twitter:title"]', { name: 'twitter:title', content: title })
    upsertMeta('meta[name="twitter:description"]', { name: 'twitter:description', content: description })

    if (image) {
      upsertMeta('meta[property="og:image"]', { property: 'og:image', content: image })
      upsertMeta('meta[name="twitter:card"]', { name: 'twitter:card', content: 'summary_large_image' })
      upsertMeta('meta[name="twitter:image"]', { name: 'twitter:image', content: image })
    } else {
      upsertMeta('meta[name="twitter:card"]', { name: 'twitter:card', content: 'summary' })
    }
  }, [description, image, path, title])
}
