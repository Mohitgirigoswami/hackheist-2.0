import { useState, useEffect } from 'react';
import { 
  Rocket, 
  Loader2, 
  GitBranch, 
  TerminalSquare, 
  ExternalLink, 
  Activity, 
  BarChart2,
  Folder,
  X,
  Server,
  Cpu
} from 'lucide-react';
import { getProjects, deployProject } from './services/api';

function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formName, setFormName] = useState('');
  const [formRepo, setFormRepo] = useState('');
  const [formSubDir, setFormSubDir] = useState('/');
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
      await deployProject(formName, formRepo, formSubDir);
      setFormName('');
      setFormRepo('');
      setFormSubDir('/');
      await fetchProjects();
    } catch (e) {
      alert("Deployment failed to start. Check console for details.");
    } finally {
      setDeploying(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'RUNNING': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]';
      case 'BUILDING': return 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse';
      case 'QUEUED': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'FAILED': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 text-white relative overflow-hidden flex flex-col items-center selection:bg-purple-500/30">
      {/* Dynamic Background with slower animations for a premium feel */}
      <div className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vw] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none transition-all duration-1000 ease-in-out" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[60vw] h-[60vw] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none " />

      <main className="w-full max-w-6xl z-10 relative flex flex-col gap-8 md:gap-12 mt-4 md:mt-8">
        
        {/* Header section styled to impress */}
        <header className="flex flex-col md:flex-row items-start md:items-center justify-between glass-card p-6 md:p-8 rounded-3xl gap-6 border border-white/5 shadow-2xl">
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/30 transform hover:scale-105 transition-transform">
              <Rocket className="w-8 h-8 text-white" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-4xl font-extrabold tracking-tight gradient-text mb-1 relative w-max">
                ZeroToDeploy
                <span className="absolute -top-1 -right-4 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
              </h1>
              <p className="text-sm md:text-base text-slate-400 font-medium">From Zero to Execution in Milliseconds.</p>
            </div>
          </div>
          <div className="flex items-center gap-3 bg-black/40 px-5 py-3 rounded-2xl border border-white/5">
            <Server className="w-5 h-5 text-blue-400" />
            <div className="flex flex-col">
              <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Engine Status</span>
              <span className="text-sm text-emerald-400 font-medium flex items-center gap-2">
                Online and Connected
              </span>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">
          
          {/* Deploy Form */}
          <section className="col-span-1 glass-card p-8 rounded-3xl flex flex-col gap-6 shadow-xl border border-white/5 relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            <div className="relative z-10">
              <h2 className="text-2xl font-bold mb-2 flex items-center gap-3 text-slate-100">
                <TerminalSquare className="w-6 h-6 text-purple-400" />
                New Deployment
              </h2>
              <p className="text-sm text-slate-400 leading-relaxed mb-8">Launch an isolated micro-container directly from a Git repository.</p>
            
              <form onSubmit={handleDeploy} className="flex flex-col gap-6">
                <div className="flex flex-col gap-2 group/input">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-slate-500 group-focus-within/input:text-purple-400 transition-colors">Project Name</label>
                  <input 
                    type="text" 
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. hackathon-alpha"
                    required
                    className="bg-black/40 border border-white/5 rounded-2xl px-5 py-4 outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 focus:bg-white/5 w-full transition-all text-sm placeholder:text-slate-600 block shadow-inner"
                  />
                </div>

                <div className="flex flex-col gap-2 group/input">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-slate-500 group-focus-within/input:text-purple-400 transition-colors">Git Repository URL</label>
                  <div className="relative">
                    <GitBranch className="w-5 h-5 absolute left-5 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within/input:text-purple-500 transition-colors" />
                    <input 
                      type="url" 
                      value={formRepo}
                      onChange={(e) => setFormRepo(e.target.value)}
                      placeholder="https://github.com/user/demo.git"
                      required
                      className="bg-black/40 border border-white/5 rounded-2xl pl-14 pr-5 py-4 outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 focus:bg-white/5 w-full transition-all text-sm placeholder:text-slate-600 shadow-inner"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2 group/input">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-slate-500 group-focus-within/input:text-purple-400 transition-colors">Subdirectory</label>
                  <div className="relative">
                    <Folder className="w-5 h-5 absolute left-5 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within/input:text-purple-500 transition-colors" />
                    <input 
                      type="text" 
                      value={formSubDir}
                      onChange={(e) => setFormSubDir(e.target.value)}
                      placeholder="/"
                      className="bg-black/40 border border-white/5 rounded-2xl pl-14 pr-5 py-4 outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 focus:bg-white/5 w-full transition-all text-sm placeholder:text-slate-600 font-mono shadow-inner"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button 
                    type="submit" 
                    disabled={deploying}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold py-4 px-4 rounded-2xl transition-all duration-300 shadow-[0_0_20px_rgba(139,92,246,0.2)] hover:shadow-[0_0_40px_rgba(139,92,246,0.6)] flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5 active:translate-y-0 border border-white/10"
                  >
                    {deploying ? <Loader2 className="w-5 h-5 animate-spin" /> : <Rocket className="w-5 h-5 group-hover:animate-bounce" />}
                    {deploying ? 'Allocating Container...' : 'Deploy to Localhost'}
                  </button>
                </div>
              </form>
            </div>
          </section>

          {/* Projects Table */}
          <section className="col-span-1 xl:col-span-2 glass-card p-8 rounded-3xl flex flex-col min-h-[550px] shadow-xl border border-white/5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[80px] rounded-full pointer-events-none" />
            
            <div className="flex items-center justify-between mb-8 relative z-10">
              <div>
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-3 text-slate-100">
                  <Activity className="w-6 h-6 text-blue-400" />
                  Container Registry
                </h2>
                <p className="text-sm text-slate-400">Live orchestration feed of your deployed environments.</p>
              </div>
            </div>

            <div className="overflow-x-auto w-full flex-grow relative z-10">
              {loading ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 gap-4 min-h-[250px]">
                  <Loader2 className="w-10 h-10 animate-spin text-purple-500" />
                  <span className="font-medium tracking-wide animate-pulse">Syncing with Track B Data...</span>
                </div>
              ) : projects.length === 0 ? (
                <div className="w-full h-[300px] flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-white/5 rounded-3xl bg-black/20 hover:bg-black/40 transition-colors">
                  <TerminalSquare className="w-14 h-14 mb-4 text-slate-600" />
                  <p className="font-medium text-slate-400 text-lg">Registry is completely empty.</p>
                  <p className="text-sm mt-2 text-slate-500">Initiate a pipeline to spin up your first application.</p>
                </div>
              ) : (
                <div className="w-full min-w-[700px]">
                  <div className="grid grid-cols-12 gap-4 pb-4 border-b border-white/10 text-[11px] font-bold uppercase tracking-widest text-slate-500 px-2">
                    <div className="col-span-3">Resource</div>
                    <div className="col-span-4">Source Layer</div>
                    <div className="col-span-2">Health</div>
                    <div className="col-span-3 text-right">Actions</div>
                  </div>
                  <div className="flex flex-col gap-3 mt-4">
                    {projects.map((project) => (
                      <div key={project.id} className="grid grid-cols-12 gap-4 items-center bg-white/[0.02] hover:bg-white/[0.04] p-5 rounded-2xl border border-transparent hover:border-white/5 transition-all group">
                        <div className="col-span-3 flex flex-col">
                          <span className="font-bold text-slate-100 text-base">{project.name}</span>
                          <span className="text-xs text-slate-500 font-mono mt-0.5" title={project.id}>id: {project.id.slice(0, 8)}</span>
                        </div>
                        <div className="col-span-4 flex flex-col gap-1.5 text-sm text-slate-400">
                          <div className="flex items-center gap-2 max-w-full" title={project.repo_url}>
                            <GitBranch className="w-4 h-4 flex-shrink-0 text-slate-600" />
                            <span className="truncate">{project.repo_url.replace('https://github.com/', '')}</span>
                          </div>
                          <div className="flex items-center gap-2 max-w-full text-xs font-mono text-purple-400/80">
                             <Folder className="w-3 h-3 flex-shrink-0" />
                             <span className="truncate">{project.sub_directory}</span>
                          </div>
                        </div>
                        <div className="col-span-2">
                          <span className={`px-3 py-1.5 rounded-full text-[11px] font-bold border flex items-center gap-2 w-max tracking-wide ${getStatusColor(project.status)}`}>
                            {project.status === 'BUILDING' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                            {project.status}
                          </span>
                        </div>
                        <div className="col-span-3 flex items-center justify-end gap-3 flex-wrap">
                          {project.status === 'RUNNING' && project.assigned_port ? (
                            <>
                              <button 
                                onClick={() => setMetricsProject(project)}
                                className="inline-flex items-center gap-2 text-[13px] text-purple-400 hover:text-white font-semibold px-4 py-2 rounded-xl bg-purple-500/10 hover:bg-purple-600 transition-all border border-purple-500/20 hover:border-transparent hover:shadow-[0_0_15px_rgba(147,51,234,0.4)]"
                              >
                                <Cpu className="w-4 h-4" /> Telemetry
                              </button>
                              <a 
                                href={`http://localhost:${project.assigned_port}`} 
                                target="_blank" 
                                rel="noreferrer"
                                className="inline-flex items-center gap-2 text-[13px] text-blue-400 hover:text-white font-semibold px-4 py-2 rounded-xl bg-blue-500/10 hover:bg-blue-600 transition-all border border-blue-500/20 hover:border-transparent hover:shadow-[0_0_15px_rgba(59,130,246,0.4)]"
                              >
                                Browse <ExternalLink className="w-4 h-4" />
                              </a>
                            </>
                          ) : (
                            <span className="text-xs font-semibold text-slate-600 tracking-wide mt-1">AWAITING ENGINE</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>

      {/* Premium Grafana Metrics Modal (Hour 7) */}
      {metricsProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-200">
          {/* Deep Blur Backdrop */}
          <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={() => setMetricsProject(null)} />
          
          <div className="relative w-full max-w-6xl bg-[#09090b] border border-white/10 rounded-3xl shadow-[0_0_100px_rgba(139,92,246,0.15)] overflow-hidden flex flex-col h-[85vh] ring-1 ring-white/10">
            
            {/* Modal Premium Header */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between px-8 py-6 border-b border-white/5 bg-slate-900/50">
              <div className="flex items-center gap-5">
                <div className="p-3.5 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-white/5 shadow-inner">
                  <Cpu className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <h3 className="font-extrabold text-2xl flex items-center gap-2 text-white tracking-tight">
                    Prometheus Telemetry
                    <span className="text-purple-400 font-medium opacity-80 text-lg">/ {metricsProject.name}</span>
                  </h3>
                  <div className="flex gap-4 text-xs text-slate-400 font-mono mt-1.5 font-medium">
                    <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> PORT: {metricsProject.assigned_port}</span>
                    <span className="opacity-30">|</span>
                    <span>INSTANCE_ID: {metricsProject.id}</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => setMetricsProject(null)}
                className="p-3 rounded-2xl bg-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-all border border-transparent hover:border-rose-500/30 absolute top-5 right-5 md:relative md:top-auto md:right-auto"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body / Seamless Kiosk Iframe */}
            <div className="flex-1 bg-[#09090b] w-full overflow-hidden relative group p-0">
              <div className="absolute inset-0 flex items-center justify-center -z-10">
                <Loader2 className="w-8 h-8 animate-spin text-purple-500/30" />
              </div>
              
              {/* Note: kiosk=1 disables Grafana's chrome completely, making it blend seamlessly into our UI */}
              <iframe 
                src={`http://localhost:3000/d/container-metrics/container-metrics?orgId=1&refresh=5s&theme=dark&var-container_name=container-${metricsProject.id}&kiosk=1`}
                width="100%" 
                height="100%" 
                frameBorder="0"
                className="w-full h-full bg-transparent opacity-0 animate-[fadeIn_0.5s_ease-in-out_1s_forwards]"
                title="Grafana Internal Dashboard"
              ></iframe>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
