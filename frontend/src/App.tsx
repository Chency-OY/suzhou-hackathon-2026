import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ComingSoonPage from "./pages/ComingSoonPage";
import ScenarioDetailPage from "./pages/ScenarioDetailPage";
import ScenarioListPage from "./pages/ScenarioListPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ScenarioListPage />} />
        <Route path="scenarios/:id" element={<ScenarioDetailPage />} />
        <Route path="session/:id" element={<ComingSoonPage title="演练" />} />
        <Route path="report/:id" element={<ComingSoonPage title="复盘报告" />} />
        <Route path="progress" element={<ComingSoonPage title="我的成长" />} />
        <Route path="team" element={<ComingSoonPage title="团队看板" />} />
        <Route path="*" element={<ComingSoonPage title="页面不存在" />} />
      </Route>
    </Routes>
  );
}
