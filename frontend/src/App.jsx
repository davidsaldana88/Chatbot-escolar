import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Chat from './componentes/Chat'
import PanelAdmin from './componentes/PanelAdmin'
import RutaProtegida from './componentes/RutaProtegida'
import Configuracion from './paginas/Configuracion'
import FormularioOpinion from './paginas/FormularioOpinion'
import Grupos from './paginas/Grupos'
import Inicio from './paginas/Inicio'
import Login from './paginas/Login'
import MateriasProfesores from './paginas/MateriasProfesores'
import Opiniones from './paginas/Opiniones'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/opiniones" element={<FormularioOpinion />} />
        <Route path="/admin/login" element={<Login />} />
        <Route
          path="/admin"
          element={
            <RutaProtegida>
              <PanelAdmin />
            </RutaProtegida>
          }
        >
          <Route index element={<Inicio />} />
          <Route path="grupos" element={<Grupos />} />
          <Route path="materias" element={<MateriasProfesores />} />
          <Route path="opiniones" element={<Opiniones />} />
          <Route path="configuracion" element={<Configuracion />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}