import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ComingSoonPage from "./pages/ComingSoonPage";
import ScenarioDetailPage from "./pages/ScenarioDetailPage";
import ScenarioListPage from "./pages/ScenarioListPage";
import SessionHistoryPage from "./pages/SessionHistoryPage";
import SessionPage from "./pages/SessionPage";
import SessionReviewPage from "./pages/SessionReviewPage";
import DiaryPage from "./pages/DiaryPage";
import RadarPage from "./pages/RadarPage";
import ProductsPage from "./pages/ProductsPage";
import ProductTestPage from "./pages/ProductTestPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ScenarioListPage />} />
        <Route path="home" element={<ScenarioListPage />} />
        <Route path="scenarios/:id" element={<ScenarioDetailPage />} />
        <Route path="session/:id" element={<SessionPage />} />
        <Route path="review/:id" element={<SessionReviewPage />} />
        <Route path="report/:id" element={<SessionReviewPage />} />
        <Route path="progress" element={<SessionHistoryPage />} />
        <Route path="diary" element={<DiaryPage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="products/:id/test" element={<ProductTestPage />} />
        <Route path="radar" element={<RadarPage />} />
        <Route path="*" element={<ComingSoonPage title="页面不存在" />} />
      </Route>
    </Routes>
  );
}
