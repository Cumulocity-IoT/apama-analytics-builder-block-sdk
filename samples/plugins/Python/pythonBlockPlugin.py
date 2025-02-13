from apama.eplplugin import EPLAction, EPLPluginBase
from RestrictedPython import compile_restricted, Eval, Guards, safe_builtins, limited_builtins, utility_builtins
class PythonBlockPlugin(EPLPluginBase):
	safe_globals = {
		"__builtins__": {**safe_builtins, **limited_builtins, **utility_builtins,
			"__name__": "restricted_python_block",
			"__metaclass__": type,
			"_getiter_": Eval.default_guarded_getiter,
			"_iter_unpack_sequence": Guards.guarded_iter_unpack_sequence,
		}
	}

	def __init__(self,init):
		super(PythonBlockPlugin,self).__init__(init)

	@EPLAction("action<string> returns chunk")
	def validate(self, expression):
		return compile_restricted(expression, '<inline code>', 'exec')

	@EPLAction("action<chunk, sequence<any>> returns sequence<any>")
	def execute(self, bytecode, v):
		locals = { "generate": False }
		for i in range(len(v)):
			locals['input'+str(i)] = v[i]
		for i in range(10):
			locals['output'+str(i)] = None
		exec(bytecode, PythonBlockPlugin.safe_globals, locals)
		result = [locals["generate"]]
		for i in range(10):
			if locals.get('output'+str(i)) != None:
				result.append(locals.get('output'+str(i)))

		return result
