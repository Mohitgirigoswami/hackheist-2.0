import { useState, useEffect } from 'react';
import { 
  Rocket, 
  Loader2, 
  GitBranch, 
  TerminalSquare, 
  ExternalLink, 
  Activity, 
  Github,
  BarChart2,
  X 
} from 'lucide-react';
import { getProjects, deployProject } from './services/api';

function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formName, setFormName] = useState('');
  const [formRepo, setFormRepo] = useState('');
  const [deploying, setDeploying] = useState(false);
  const [metricsProject, setMetricsProject] = useState(null);

  const fetchProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data.projects || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 3000); 
    return () => clearInterval(interval);
  }, []);

  const handleDeploy = async (e) => {
    e.preventDefault();
    if (!formName || !formRepo) return;
    setDeploying(true);
    try {
      await deployProject(formName, formRepo);
      setFormName('');
      setFormRepo('');
      await fetchProjects();
    } catch (e) {
      alert("Deployment failed to start. Check console for details.");
    } finally {
      setDeploying(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'RUNNING': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'BUILDING': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'QUEUED': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'FAILED': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="min-h-screen p-8 text-white relative overflow-hidden flex flex-col items-center">
      {/* Dynamic Background */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-purple-600/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-blue-600/20 blur-[120px] rounded-full pointer-events-none" />

      <main className="w-full max-w-6xl z-10 relative flex flex-col gap-10 mt-10">
        
        {/* Header section */}
        <header className="flex items-center justify-between glass-card p-6 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <Rocket className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight">Code Catalyst</h1>
              <p className="text-sm text-slate-400 font-medium">Local-First Vercel Clone</p>
            </div>
          </div>
          <a href="https://github.com" target="_blank" rel="noreferrer" className="glass p-3 rounded-full hover:bg-white/10 transition-colors">
            <Github className="w-5 h-5" />
          </a>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* Deploy Form */}
          <section className="col-span-1 glass-card p-8 rounded-3xl flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                <TerminalSquare className="w-5 h-5 text-purple-400" />
                New Deployment
              </h2>
              <p className="text-sm text-slate-400">Deploy your repository instantly within an isolated container.</p>
            </div>
            
            <form onSubmit={handleDeploy} className="flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Project Name</label>
                <input 
                  type="text" 
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. my-awesome-app"
                  required
                  className="bg-black/40 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-purple-500 w-full transition-all text-sm placeholder:text-slate-600"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Git Repository URL</label>
                <div className="relative">
                  <GitBranch className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input 
                    type="url" 
                    value={formRepo}
                    onChange={(e) => setFormRepo(e.target.value)}
                    placeholder="https://github.com/user/repo"
                    required
                    className="bg-black/40 border border-white/10 rounded-xl pl-11 pr-4 py-3 outline-none focus:border-purple-500 w-full transition-all text-sm placeholder:text-slate-600"
                  />
                </div>
              </div>

              <button 
                type="submit" 
                disabled={deploying}
                className="mt-2 w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-400 hover:to-blue-400 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deploying ? <Loader2 className="w-5 h-5 animate-spin" /> : <Rocket className="w-5 h-5" />}
                {deploying ? 'Initializing...' : 'Deploy Now'}
              </button>
            </form>
          </section>

          {/* Projects Table */}
          <section className="col-span-1 lg:col-span-2 glass-card p-8 rounded-3xl flex flex-col min-h-[480px]">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  Active Projects
                </h2>
                <p className="text-sm text-slate-400">Live view of your containerized applications.</p>
              </div>
            </div>

            <div className="overflow-x-auto w-full flex-grow">
              {loading ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 gap-3 min-h-[200px]">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                  Loading projects...
                </div>
              ) : projects.length === 0 ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 min-h-[200px] border border-dashed border-white/10 rounded-2xl bg-black/20">
                  <TerminalSquare className="w-12 h-12 mb-4 opacity-50" />
                  <p>No deployments yet.</p>
                  <p className="text-sm mt-1">Deploy an app to see it here.</p>
                </div>
              ) : (
                <table className="w-full text-left border-separate border-spacing-y-3">
                  <thead>
                    <tr className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      <th className="pb-3 px-4 font-medium">Project</th>
                      <th className="pb-3 px-4 font-medium">Repository</th>
                      <th className="pb-3 px-4 font-medium">Status</th>
                      <th className="pb-3 px-4 font-medium text-right">View</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((project) => (
                      <tr key={project.id} className="group">
                        <td className="px-4 py-4 glass rounded-l-xl border-r-0">
                          <div className="font-semibold text-slate-100">{project.name}</div>
                          <div className="text-xs text-slate-500 font-mono mt-1 w-24 truncate" title={project.id}>{project.id}</div>
                        </td>
                        <td className="px-4 py-4 glass border-l-0 border-r-0 text-sm text-slate-400">
                          <div className="flex items-center gap-2 truncate max-w-[200px]" title={project.repo_url}>
                            <GitBranch className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{project.repo_url.replace('https://github.com/', '')}</span>
                          </div>
                        </td>
                        <td className="px-4 py-4 glass border-l-0 border-r-0">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-2 w-max ${getStatusColor(project.status)}`}>
                            {project.status === 'BUILDING' && <Loader2 className="w-3 h-3 animate-spin" />}
                            {project.status}
                          </span>
                        </td>
                        <td className="px-4 py-4 glass rounded-r-xl border-l-0 text-right">
                          {project.status === 'RUNNING' && project.assigned_port ? (
                            <div className="flex items-center justify-end gap-2">
                              <button 
                                onClick={() => setMetricsProject(project)}
                                className="inline-flex items-center gap-2 text-sm text-purple-400 hover:text-purple-300 font-medium px-3 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 transition-colors"
                              >
                                <BarChart2 className="w-4 h-4" /> Metrics
                              </button>
                              <a 
                                href={`http://localhost:${project.assigned_port}`} 
                                target="_blank" 
                                rel="noreferrer"
                                className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 font-medium px-3 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 transition-colors"
                              >
                                Visit <ExternalLink className="w-4 h-4" />
                              </a>
                            </div>
                          ) : (
                            <span className="text-sm text-slate-600 cursor-not-allowed">--</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        </div>
      </main>

      {/* Grafana Metrics Modal */}
      {metricsProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMetricsProject(null)} />
          <div className="relative w-full max-w-5xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[80vh] border-t-purple-500/30 border-t-2">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-800/80">
              <div className="flex items-center gap-3">
                <div className="glass p-2 rounded-lg">
                  <BarChart2 className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    System Metrics 
                    <span className="text-slate-400 font-normal">/ {metricsProject.name}</span>
                  </h3>
                  <div className="flex gap-2 text-xs text-slate-400 font-mono mt-0.5">
                    <span className="bg-black/30 px-2 py-0.5 rounded">Port: {metricsProject.assigned_port}</span>
                    <span className="bg-black/30 px-2 py-0.5 rounded">ID: {metricsProject.id.slice(0, 8)}...</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => setMetricsProject(null)}
                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body / Iframe */}
            <div className="flex-1 bg-black p-4">
              <iframe 
                src={`http://localhost:3000/d/container-metrics/container-metrics?orgId=1&refresh=5s&theme=dark&var-container_name=container-${metricsProject.id}&kiosk=1`}
                width="100%" 
                height="100%" 
                frameBorder="0"
                className="rounded-xl border border-white/5 bg-slate-900"
                title="Grafana Dashboard"
              ></iframe>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
