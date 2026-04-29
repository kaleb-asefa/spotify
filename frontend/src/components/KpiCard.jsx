import { motion } from "framer-motion";

export default function KpiCard({ label, value, accent }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="kpi-card"
      style={{ borderColor: accent }}
    >
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>
      <span className="kpi-glow" style={{ background: accent }} />
    </motion.article>
  );
}
