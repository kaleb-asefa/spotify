import { motion } from "framer-motion";

export default function SectionCard({ title, children, delay = 0 }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="section-card"
    >
      <header className="section-header">
        <h3>{title}</h3>
      </header>
      {children}
    </motion.section>
  );
}
