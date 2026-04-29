export default function MediaThumb({ imageUrl, altText, fallbackText }) {
  if (imageUrl) {
    return <img src={imageUrl} alt={altText} className="media-thumb" loading="lazy" />;
  }

  const initial = (fallbackText || "?").trim().charAt(0).toUpperCase() || "?";
  return <div className="media-thumb media-thumb-fallback">{initial}</div>;
}
