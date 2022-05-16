import streamlit as st
from utilities import Dimensjonering, Forside, Gis, Energibronn, Strompriser, Temperaturdata, Energibehov, Kostnader, Co2, Veienvidere, load_lottie, set_bg
from streamlit_lottie import st_lottie

#--Innstillinger--
forside_obj = Forside()
forside_obj.innstillinger()
#--Innstillinger--

 
def main ():
    #--Forside--
    col1, col2, col3 = st.columns(3)
    with col1:
        forside_obj.av_logo()  
    with col2:
        st.title("Bergvarmekalkulatoren")
        st.write('Kalkuler din gevinst ved å hente energi fra berggrunnen!')
    adresse, bolig_areal = forside_obj.input()
    st.markdown("""---""")
    #--Forside--


    #--Forklaringer--
    if not adresse:
        st.header('Hva er bergvarme?')
        st.write(""" Bergvarme er i hovedsak lagret solenergi som har en 
                        stabil temperatur i størrelsesorden rundt 5 til 7 °C. For å hente ut bergvarme fra grunnen
                        må det bores en energibrønn. Inne i energibrønnen monteres det en U-formet plastslange som fylles med en sirkulerende
                        frostsikker væske. Væsken varmes opp av berggrunnen, og varmeenergien kan nå utnyttes ved hjelp av en 
                        væske-vann-varmepumpe for å levere høy temperatur til boligens vannbårne varmesystem. """) 

        st.header('Hvorfor bergvarme?')
        st.write(""" Bergvarme er både miljøvennlig, kortreist og fornybar energi, 
                        og blir stadig mer populært blant norske byggeiere. Et bergvarmeanlegg gir den 
                        beste energibesparelsen og kan redusere din strømregning med en faktor på 3 – 4. """)
        st.write(""" Om sommeren, når det er behov for kjøling, er temperaturen i brønnen i seg selv
                        lav nok til å kjøle bygningen. Da trengs viftekonvektorer som kan 
                        fordele kjøling i bygningen på en komfortabel måte. """)

        st.header('Hva gjør bergvarmekalkulatoren?')
        st.write(""" Kalkulatoren er utviklet av Asplan Viak AS, og utfører en enkel dimensjonering av en energibrønn 
        med bergvarmepumpe for din bolig. Den regner så ut kostnader og miljøgevinst for det aktuelle anlegget. Det er mulig 
        å justere parameterene som ligger til grunn for beregningen i menyen til venstre som dukker opp når du skriver inn din adresse. """)
        st.write(""" Resultatene fra kalkulatoren er å anse som et estimat, og endelig dimensjonering av energibrønnen med varmepumpe
        bør tilpasses de stedlige forholdene av leverandør. """)

        st.header('Om Asplan Viak')
        st.write(""" Asplan Viak er et av Norges ledende rådgivningsselskaper innen plan, 
        arkitektur- og ingeniørfag. Vår kompetanse finner du fra Tromsø i nord til 
        Kristiansand i sør, med 1200+ medarbeidere fordelt på 32 kontorer. """)

        st.write(""" Asplan Viak har solid kompetanse på både lukkede systemer med energibrønner i fjell, 
        åpne systemer med bruk av grunnvann som energikilde, og større energilager. 
        Vi tilbyr en rekke tjenester innen disse fagområdene, alt fra større utredninger 
        og utviklingsprosjekter til forundersøkelser og detaljprosjektering av energibrønnparker. 
        Vår erfaring er at tidlig og god planlegging, gjennomtenkte løsninger, gode grunnlagsdata og fokus 
        på oppfølging i bygge- og driftsfasen er de største suksesskriteriene for vellykkede grunnvarmeanlegg. """)

        st_lottie(load_lottie('https://assets5.lottiefiles.com/packages/lf20_l22gyrgm.json'))  
        st.caption('Et verktøy fra Asplan Viak AS | 📧 magne.syljuasen@asplanviak.no')
    #--Forklaringer--


    #--Appen--
    if adresse:
        adresse_lat, adresse_long = Gis().adresse_til_koordinat(adresse)
        dybde_til_fjell, energibronn_lat, energibronn_long = Energibronn(adresse_lat, adresse_long).dybde_til_fjell()
        temperaturdata_obj = Temperaturdata(adresse_lat,adresse_long)
        stasjon_id, stasjon_lat, stasjon_long, distanse_min = temperaturdata_obj.nearmeste_stasjon()
        #st.write (temperaturdata_obj.gjennomsnittstemperatur())

        st.title('Resultater')
        st.header('Oversiktskart')
        Gis().kart(stasjon_lat, adresse_lat, energibronn_lat, stasjon_long, adresse_long, energibronn_long)
        with st.expander ('Hva viser kartet?'):
            st.write (""" Kartet viser adresse (rød sirkel), nærmeste eksisterende energibrønn (grønn sirkel) 
            og nærmeste værstasjon med fullstendige temperaturdata (blå sirkel). Nærmeste eksisterende 
            energibrønn brukes til å estimere dybde til fjell i området. Fra værstasjonen hentes det 
            inn målt temperatur per time for de siste 4 år. """)

        #--Sidebar--
        with st.sidebar:
            st.markdown(""" Verdiene under er basert på oppgitt adresse og areal, 
            og ligger til grunn for beregningen. Disse kan justeres ved behov """)
        #--Sidebar--

        energibehov_obj = Energibehov()
        dhw_arr, romoppvarming_arr = energibehov_obj.totalt_behov_fra_fil(stasjon_id, bolig_areal)
        dhw_sum, romoppvarming_sum, energibehov_sum = energibehov_obj.aarlig_behov(dhw_arr, romoppvarming_arr)

        #--Sidebar--
        with st.sidebar:
            dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr = energibehov_obj.juster_behov(dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr)
        #--Sidebar--

        st.header('Oppvarmingsbehov for din bolig')
        energibehov_obj.plot(dhw_arr, romoppvarming_arr)
        energibehov_obj.resultater(dhw_sum, romoppvarming_sum, energibehov_sum)
        with st.expander ('Hvordan beregnes oppvarmingsbehovet?'):
            st.write (""" Gjennomsnittstemperatur fra de siste 4 år og oppgitt boligareal benyttes til å estimere 
            oppvarmingsbehovet for din bolig. Beregningen gjøres ved hjelp av PROFet-verktøyet som er utviklet av Sintef. 
            Verktøyet estimerer både det årlige behovet for romoppvarming- og varmtvann som til sammen
            utgjør det totale årlige oppvarmingsbehovet for din bolig. """)

        energibehov_arr = (dhw_arr + romoppvarming_arr).reshape(-1)
        dimensjonering_obj = Dimensjonering()

        #--Sidebar--
        with st.sidebar:       
            dekningsgrad = dimensjonering_obj.angi_dekningsgrad()
            cop = dimensjonering_obj.angi_cop()
        #--Sidebar--

        energibehov_arr_gv, energibehov_sum_gv, varmepumpe_storrelse = dimensjonering_obj.energi_og_effekt_beregning(dekningsgrad, energibehov_arr, energibehov_sum)
        levert_fra_bronner_arr, kompressor_arr, spisslast_arr, levert_fra_bronner_sum, kompressor_sum, spisslast_sum = dimensjonering_obj.dekning(energibehov_arr_gv, energibehov_arr, cop)
        antall_meter = dimensjonering_obj.antall_meter(varmepumpe_storrelse, levert_fra_bronner_sum, cop)
        antall_bronner = dimensjonering_obj.antall_bronner (antall_meter)

        st.header('Dimensjonering av ditt bergvarmeanlegg') 
        #dimensjonering_obj.varighetsdiagram_bar(spisslast_arr, energibehov_arr_gv, kompressor_arr, levert_fra_bronner_arr)
        dimensjonering_obj.varighetsdiagram(energibehov_arr, energibehov_arr_gv, kompressor_arr)
        dimensjonering_obj.bronn_resultater(antall_meter, varmepumpe_storrelse, antall_bronner)

        with st.expander('Hva ligger til grunn for denne dimensjoneringen?'):
            st.write(""" Effektvarighetsdiagrammet i figuren over viser hvor stor andel av energibehovet som dekkes av en effekt. 
            Størrelsen på varmepumpen bestemmes ut ifra maksimumeffekten i dette diagrammet. """)
            st.write(""" For å bestemme antall brønnmetere må energibehovet hensyntas. En vanlig feil er at 
            energibrønnen dimensjoneres etter størrelsen på varmepumpen. Årsvarmefaktoren til varmepumpen 
            angir hvor stor del av energibehovet som kan leveres fra energibrønnen og andelen strøm. 
            Energien som leveres energibrønnen er vist med grønn farge i diagrammet, og strømforbuket i mørkegrønn farge.
            Erfaring tilsier at en energibrønn kan levere ca. 80 kWh/m. Totalt antall brønnmetere er beregnet ut ifra dette. """)

        strompriser_obj = Strompriser()

        #--Sidebar--
        with st.sidebar:   
            strompriser_obj.input()
        #--Sidebar--

        el_pris = strompriser_obj.beregn_el_pris()
        kostnader_obj = Kostnader(dybde_til_fjell, varmepumpe_storrelse, antall_meter, kompressor_arr, energibehov_arr_gv, el_pris)
        
        #--Sidebar--
        with st.sidebar:   
            kostnader_obj.oppdater_dybde_til_fjell()
        #--Sidebar--

        st.header ('Bergvarme reduserer din månedlige strømregning')
        kostnader_obj.monthly_costs()
        with st.expander('Hvordan beregnes dette?'):
            st.write(""" Et bergvarmeanlegg gir en god energibesparelse som bestemmes av 
            årsvarmefaktoren til varmepumpen. Den faktiske besparelsen i kroner vil være avhengig av strømprisen.
            I denne beregningen er det lagt til grunn en fast strømpris per time i et år som kan velges i menyen til venstre.
            Vi vet ikke hvordan strømprisen kommer til å utvikle seg i fremtiden, men for hver økning i strømpris vil bergvarme
            bli 3 - 4 ganger mer lønnsomt. """)

        st.header ('Årlig kostnadsutvikling')
        kostnader_obj.plot_investeringskostnad()
        with st.expander('Investeringskostnad'):
            st.write (""" Den største barrieren når det gjelder etablering av 
            bergvarmeanlegg er investeringskostnaden. Investeringskostnaden inkluderer 
            boring av energibrønn samt installasjon av varmepumpe. Det presiseres at 
            dette kun er et anslag, og endelig pris må bestemmes av leverandør. """)
            st.write(""" Enovatilskuddet er en støtteordning for private husholdninger der du
            kan få inntil 10 000 kr i støtte når du anskaffer en bergvarmepumpe (væske-vann-varmepumpe). """)
            st.write(""" Grønne energilån er lån til miljøvennlige og energibesparende tiltak. Med et slikt lån
            kan dermed investeringskostnaden fordeles utover flere år. I mange tilfeller vil den månedlige 
            besparelsen med drift av et bergvarmeanlegg kunne forrente et slikt lån. """)

        st.header ('Et miljøvennlig alternativ')
        Co2().beregning(energibehov_arr, kompressor_sum)
        with st.expander ('Hvordan beregnes dette?'):
            st.write(""" NVE publiserer hvert år klimadeklarasjon for fysisk levert strøm i Norge. Det 
            gjennomsnittlige direkte klimagassutslippet knyttet til bruk av strøm i Norge
            var 8 gram CO2-ekvivalenter per kilowattime i 2020. Denne verdien ligger til grunn for beregningen. """)

        st.markdown("""---""")
        st.title('Veien videre')
        Veienvidere()
        st.caption('Et verktøy fra Asplan Viak AS | 📧 magne.syljuasen@asplanviak.no')
        #--Appen--

main ()
