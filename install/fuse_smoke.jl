using FUSE
using JSON

ini, act = FUSE.case_parameters(:FPP)
dd = FUSE.init(ini, act)

println("FUSE import/init OK")
println("JSON import OK")
println("FUSE package path: ", pkgdir(FUSE))
println("FUSE smoke dd type: ", typeof(dd))
