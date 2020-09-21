classdef cellManager < handle
    %CELLMANAGER Manages all agent types of his cell
    %   The cellular approach divides the energy system into several energy cells.
    %   According to this approach the energy system of ensysim is build up. The
    %   cell manager agent represents such an energy cell and registers the energy
    %   loads of all agents attached to his cell.

    properties
        % number of specific agents
        nPHHconsumer_e
        % agent objects
        PHHconsumer_e
        % resulting balance
        currentEnergyBalance_e  % Wh
        currentEnergyBalance_t  % Wh
    end

    methods
        function self = cellManager(nPHHconsumer_e,...
                                    normSLP, PHH_COC_distribution)
            self.PHHconsumer_e = PHHconsumer_e(nPHHconsumer_e, ...
                                               normSLP, PHH_COC_distribution);
            self.currentEnergyBalance_e = 0;
        end

        function self = update(self, timeIdx)
            self.PHHconsumer_e.update(timeIdx);
            self.currentEnergyBalance_e = self.PHHconsumer_e.currentEnergyBalance_e;
        end
    end
end

