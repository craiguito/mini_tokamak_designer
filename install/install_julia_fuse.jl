using Pkg

function add_registry_if_needed(spec)
    try
        Pkg.Registry.add(spec)
    catch err
        @warn "Registry add skipped or failed; continuing because the registry may already exist" spec exception=(err, catch_backtrace())
    end
end

add_registry_if_needed(Pkg.RegistrySpec(url="https://github.com/ProjectTorreyPines/FuseRegistry.jl.git"))
add_registry_if_needed("General")
Pkg.add("FUSE")
Pkg.add("JSON")
using FUSE
using JSON

ini, act = FUSE.case_parameters(:FPP)
dd = FUSE.init(ini, act)

println("FUSE import/init OK")
println("JSON import OK")
println("FUSE package path: ", pkgdir(FUSE))
println("FUSE smoke dd type: ", typeof(dd))
